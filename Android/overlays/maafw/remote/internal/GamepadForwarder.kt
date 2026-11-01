package com.aliothmoon.maafw.remote.internal

import android.os.SystemClock
import android.system.Os
import android.system.OsConstants
import android.view.InputDevice
import com.aliothmoon.maafw.third.Ln
import com.aliothmoon.maafw.third.wrappers.ServiceManager
import com.sun.jna.Library
import com.sun.jna.Native
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream

/**
 * 后台模式下实体手柄跟着主屏焦点，进不了虚拟屏上的鸣潮。
 *
 * 优先：把物理 Xbox 的 descriptor 关联到游戏虚拟屏（Joystick/Key 都按关联 display 派发），
 * 不 grab、不重映射，键位与摇杆保持系统原样。
 *
 * 关联失败时退回：grab 物理设备 → uinput 镜像 → 关联虚拟设备。
 */
object GamepadForwarder {
    private const val TAG = "GamepadForwarder"
    private const val EVENT_SIZE = 24
    private const val EVIOCGRAB = 0x40044590
    private const val RETRY_MS = 2000L
    private const val HEARTBEAT_MS = 3000L
    private const val PROBE = "/data/local/tmp/maaww-gamepad.log"
    private const val XBOX_NAME = "Xbox Wireless Controller"
    private val EVENT_NODE = Regex("event\\d+")

    @Volatile
    private var running = false
    private var thread: Thread? = null
    private var stickThread: Thread? = null
    @Volatile
    private var fallbackDisplayId = -1
    private var associatedDescriptor: String? = null

    /** Go agent writes `x y hold_ms` here; this process (shell/input) pumps Xbox ABS. */
    private const val STICK_CMD = "/data/local/tmp/maaww_stick"

    fun start(displayId: Int) {
        if (displayId <= 0) return
        fallbackDisplayId = displayId
        if (running) {
            Ln.i("$TAG: already running, rebind display=$displayId")
            bindDescriptorToDisplay(findXboxDescriptor(), displayId)
            if (stickThread?.isAlive != true) {
                stickThread = Thread({ stickPumpLoop() }, "gamepad-stick-pump").also { it.start() }
            }
            return
        }
        running = true
        thread = Thread({ runLoop() }, "gamepad-forward").also { it.start() }
        stickThread = Thread({ stickPumpLoop() }, "gamepad-stick-pump").also { it.start() }
    }

    fun stop() {
        running = false
        thread?.interrupt()
        thread = null
        stickThread?.interrupt()
        stickThread = null
        fallbackDisplayId = -1
        unbind()
        injectAxisNeutral()
    }

    private fun probe(msg: String) {
        Ln.i("$TAG: $msg")
        runCatching {
            FileOutputStream(File(PROBE), true).use { out ->
                out.write("${System.currentTimeMillis()} $msg\n".toByteArray())
            }
        }
    }

    private fun runLoop() {
        probe("loop start fallbackDisplay=$fallbackDisplayId")
        while (running && !Thread.currentThread().isInterrupted) {
            val displayId = resolveDisplay()
            val desc = findXboxDescriptor()
            if (desc != null && bindDescriptorToDisplay(desc, displayId)) {
                probe("native associate OK, waiting (no grab/reinject)")
                var boundDisplay = displayId
                // 心跳保持关联；物理事件由系统直接送到虚拟屏
                while (running && !Thread.currentThread().isInterrupted) {
                    sleepQuiet(HEARTBEAT_MS)
                    val nowDisplay = resolveDisplay()
                    if (nowDisplay != boundDisplay || associatedDescriptor != desc) {
                        if (bindDescriptorToDisplay(desc, nowDisplay)) {
                            boundDisplay = nowDisplay
                        }
                    }
                }
                break
            }
            probe("native associate unavailable, fallback to uinput mirror")
            val path = findXboxNode()
            if (path == null) {
                probe("Xbox node not found, retry")
                sleepQuiet(RETRY_MS)
                continue
            }
            mirrorWithUinput(path)
            if (running) sleepQuiet(RETRY_MS)
        }
        unbind()
        probe("loop end")
        running = false
    }

    private fun mirrorWithUinput(path: String) {
        val displayId = resolveDisplay()
        probe("uinput mirror $path display=$displayId")
        val virtual = UInputGamepad.create() ?: run {
            probe("uinput create failed")
            return
        }
        try {
            SystemClock.sleep(400)
            val vdesc = findInputDescriptorByName(UInputGamepad.NAME)
            if (vdesc == null || !bindDescriptorToDisplay(vdesc, displayId)) {
                probe("bind virtual pad failed")
            }
            // 关掉物理设备枚举侧，避免游戏仍握着 Controller 1（已被 grab、轴冻住）
            disableInputDeviceByName(XBOX_NAME)
            val fd = Os.open(path, OsConstants.O_RDONLY, 0)
            try {
                grab(fd)
                FileInputStream(fd).use { input ->
                    val buf = ByteArray(EVENT_SIZE)
                    var n = 0
                    while (running && !Thread.currentThread().isInterrupted) {
                        if (!readFully(input, buf)) break
                        virtual.writeEvent(buf)
                        n++
                        if (n == 1 || n % 200 == 0) probe("uinput forwarded $n")
                    }
                }
            } finally {
                runCatching { Os.close(fd) }
            }
        } catch (e: Exception) {
            if (running) probe("uinput mirror failed: ${e.message}")
        } finally {
            enableInputDeviceByName(XBOX_NAME)
            unbind()
            virtual.destroy()
        }
    }

    private fun bindDescriptorToDisplay(descriptor: String?, displayId: Int): Boolean {
        if (descriptor.isNullOrEmpty() || displayId <= 0) return false
        val uniqueId = displayUniqueId(displayId) ?: return false
        return try {
            if (associatedDescriptor != null && associatedDescriptor != descriptor) {
                unbind()
            }
            ServiceManager.getInputManager().addUniqueIdAssociationByDescriptor(descriptor, uniqueId)
            associatedDescriptor = descriptor
            probe("associated $descriptor -> $uniqueId (display=$displayId)")
            true
        } catch (e: Exception) {
            probe("associate failed: ${e.message}")
            false
        }
    }

    private fun unbind() {
        val desc = associatedDescriptor ?: return
        associatedDescriptor = null
        runCatching {
            ServiceManager.getInputManager().removeUniqueIdAssociationByDescriptor(desc)
            probe("removed association $desc")
        }
    }

    private fun displayUniqueId(displayId: Int): String? =
        try {
            ServiceManager.getDisplayManager().getDisplayInfo(displayId)?.uniqueId()
        } catch (e: Exception) {
            probe("getDisplayInfo failed: ${e.message}")
            null
        }

    private fun findXboxDescriptor(): String? = findInputDescriptorByName(XBOX_NAME)

    private fun findInputDescriptorByName(name: String): String? =
        try {
            val im = ServiceManager.getInputManager().manager
            for (id in im.inputDeviceIds) {
                val device: InputDevice = im.getInputDevice(id) ?: continue
                if (device.name == name) return device.descriptor
            }
            null
        } catch (e: Exception) {
            probe("list InputDevice failed: ${e.message}")
            null
        }

    private fun disableInputDeviceByName(name: String) {
        runCatching {
            val im = ServiceManager.getInputManager().manager
            for (id in im.inputDeviceIds) {
                val device = im.getInputDevice(id) ?: continue
                if (device.name == name) {
                    im.javaClass.getMethod("disableInputDevice", Int::class.javaPrimitiveType)
                        .invoke(im, id)
                    probe("disabled InputDevice id=$id name=$name")
                }
            }
        }.onFailure { probe("disableInputDevice failed: ${it.message}") }
    }

    private fun enableInputDeviceByName(name: String) {
        runCatching {
            val im = ServiceManager.getInputManager().manager
            for (id in im.inputDeviceIds) {
                val device = im.getInputDevice(id) ?: continue
                if (device.name == name) {
                    im.javaClass.getMethod("enableInputDevice", Int::class.javaPrimitiveType)
                        .invoke(im, id)
                    probe("enabled InputDevice id=$id name=$name")
                }
            }
        }
    }

    private fun resolveDisplay(): Int {
        val vd = VirtualDisplayManager.getDisplayId()
        return if (vd > 0) vd else fallbackDisplayId
    }

    private fun grab(fd: java.io.FileDescriptor) {
        try {
            val fdNum = fdToInt(fd)
            val rc = LibcIoctl.INSTANCE.ioctl(fdNum, EVIOCGRAB, 1)
            probe(if (rc == 0) "grabbed physical fd=$fdNum" else "grab rc=$rc errno=${Native.getLastError()}")
        } catch (e: Exception) {
            probe("grab failed ${e.message}")
        }
    }

    private fun fdToInt(fd: java.io.FileDescriptor): Int {
        val method = java.io.FileDescriptor::class.java.getDeclaredMethod("getInt$")
        method.isAccessible = true
        return method.invoke(fd) as Int
    }

    private interface LibcIoctl : Library {
        fun ioctl(fd: Int, request: Int, arg: Int): Int

        companion object {
            val INSTANCE: LibcIoctl = Native.load("c", LibcIoctl::class.java)
        }
    }

    private fun findXboxNode(): String? {
        val text = runCatching { File("/proc/bus/input/devices").readText() }.getOrNull() ?: return null
        var nameMatched = false
        for (line in text.lineSequence()) {
            if (line.startsWith("N:") && line.contains(XBOX_NAME)) {
                nameMatched = true
            } else if (nameMatched && line.startsWith("H:")) {
                return EVENT_NODE.find(line)?.value?.let { "/dev/input/$it" }
            } else if (nameMatched && line.isBlank()) {
                nameMatched = false
            }
        }
        return null
    }

    private fun readFully(input: FileInputStream, buf: ByteArray): Boolean {
        var off = 0
        while (off < buf.size) {
            val n = input.read(buf, off, buf.size - off)
            if (n < 0) return false
            off += n
        }
        return true
    }

    private fun sleepQuiet(ms: Long) {
        try {
            Thread.sleep(ms)
        } catch (_: InterruptedException) {
            Thread.currentThread().interrupt()
        }
    }

    /**
     * Go `WalkToTacetTreasure` 等无法直接 sendevent（app uid 无 input 权限）。
     * 约定：agent 写入 STICK_CMD 一行 `absX absY holdMs`（ABS 原始值，Y 负=前进），
     * 本线程以 shell 权限泵到 Xbox 节点后清空文件。
     */
    private fun stickPumpLoop() {
        probe("stick pump start")
        val file = File(STICK_CMD)
        while (running && !Thread.currentThread().isInterrupted) {
            try {
                if (file.isFile && file.length() > 0) {
                    val line = file.readText().trim().lines().firstOrNull().orEmpty()
                    file.writeText("")
                    val parts = line.split(Regex("\\s+"))
                    if (parts.size >= 2) {
                        val x = parts[0].toIntOrNull() ?: 0
                        val y = parts[1].toIntOrNull() ?: 0
                        val hold = (parts.getOrNull(2)?.toLongOrNull() ?: 280L).coerceIn(50L, 2000L)
                        if (injectAxis(x, y)) {
                            sleepQuiet(hold)
                            injectAxisNeutral()
                        }
                    }
                } else {
                    sleepQuiet(20)
                }
            } catch (t: Throwable) {
                if (t is InterruptedException) {
                    Thread.currentThread().interrupt()
                    break
                }
                probe("stick pump err: ${t.message}")
                sleepQuiet(100)
            }
        }
        injectAxisNeutral()
        probe("stick pump end")
    }

    /** Left stick ABS_X / ABS_Y. Values typically ±20000..±30000. */
    @JvmStatic
    fun injectAxis(absX: Int, absY: Int): Boolean {
        val path = findXboxNode() ?: run {
            probe("injectAxis: Xbox node missing")
            return false
        }
        return runCatching {
            sendevent(path, 3, 0, absX) // ABS_X
            sendevent(path, 3, 1, absY) // ABS_Y
            sendevent(path, 0, 0, 0) // SYN
            true
        }.getOrElse {
            probe("injectAxis failed: ${it.message}")
            false
        }
    }

    @JvmStatic
    fun injectAxisNeutral() {
        injectAxis(0, 0)
    }

    /**
     * 把 Android KEYCODE_* 写成物理 Xbox 的 EV_KEY。
     * injectInputEvent(deviceId=-1) 进不了鸣潮「切换至控制器模式」；
     * 只有 Xbox Wireless Controller 节点上的按键能弹窗（见 tools/touch-review/input_mode.py）。
     * 本进程是 shell（input 组），可对 /dev/input/event* 做 sendevent。
     */
    @JvmStatic
    fun injectAndroidKey(androidKeyCode: Int, down: Boolean): Boolean {
        val linux = androidToLinux[androidKeyCode] ?: return false
        val path = findXboxNode() ?: run {
            probe("injectAndroidKey: Xbox node missing key=$androidKeyCode")
            return false
        }
        val value = if (down) 1 else 0
        return runCatching {
            sendevent(path, 1, linux, value)
            sendevent(path, 0, 0, 0)
            true
        }.getOrElse {
            probe("injectAndroidKey failed key=$androidKeyCode down=$down: ${it.message}")
            false
        }
    }

    private fun sendevent(path: String, type: Int, code: Int, value: Int) {
        val proc = ProcessBuilder("sendevent", path, type.toString(), code.toString(), value.toString())
            .redirectErrorStream(true)
            .start()
        val rc = proc.waitFor()
        if (rc != 0) {
            val err = proc.inputStream.bufferedReader().readText()
            throw IllegalStateException("sendevent rc=$rc $err")
        }
    }

    // Android KeyEvent → Linux BTN_*（与 Odin Xbox 节点一致）
    private val androidToLinux = mapOf(
        android.view.KeyEvent.KEYCODE_BUTTON_A to 304, // BTN_SOUTH
        android.view.KeyEvent.KEYCODE_BUTTON_B to 305, // BTN_EAST
        android.view.KeyEvent.KEYCODE_BUTTON_C to 306, // BTN_C
        android.view.KeyEvent.KEYCODE_BUTTON_X to 307, // BTN_NORTH
        android.view.KeyEvent.KEYCODE_BUTTON_Y to 308, // BTN_WEST
        android.view.KeyEvent.KEYCODE_BUTTON_Z to 309, // BTN_Z
        android.view.KeyEvent.KEYCODE_BUTTON_L1 to 310, // BTN_TL
        android.view.KeyEvent.KEYCODE_BUTTON_R1 to 311, // BTN_TR
        android.view.KeyEvent.KEYCODE_BUTTON_L2 to 312, // BTN_TL2
        android.view.KeyEvent.KEYCODE_BUTTON_R2 to 313, // BTN_TR2
        android.view.KeyEvent.KEYCODE_BUTTON_SELECT to 314, // BTN_SELECT
        android.view.KeyEvent.KEYCODE_BUTTON_START to 315, // BTN_START
        android.view.KeyEvent.KEYCODE_BUTTON_MODE to 316, // BTN_MODE
        android.view.KeyEvent.KEYCODE_BUTTON_THUMBL to 317, // BTN_THUMBL
        android.view.KeyEvent.KEYCODE_BUTTON_THUMBR to 318, // BTN_THUMBR
        android.view.KeyEvent.KEYCODE_DPAD_UP to 544, // BTN_DPAD_UP
        android.view.KeyEvent.KEYCODE_DPAD_DOWN to 545,
        android.view.KeyEvent.KEYCODE_DPAD_LEFT to 546,
        android.view.KeyEvent.KEYCODE_DPAD_RIGHT to 547,
    )
}
