package com.aliothmoon.maafw.remote.internal

/**
 * One line of the Go → GamepadForwarder stick protocol (`/data/local/tmp/maaww_stick`).
 *
 *  - `lx ly`                 left stick, default hold
 *  - `lx ly holdMs`          left stick (legacy, what older agents write)
 *  - `lx ly rx ry holdMs`    left stick + right stick (camera yaw/pitch)
 *
 * Values are raw Xbox ABS (±32767). Y negative = forward. Right stick X = ABS_Z (yaw, + = right),
 * right stick Y = ABS_RZ (pitch). Pure Kotlin so it can be unit-tested without Android.
 */
data class StickCommand(
    val lx: Int,
    val ly: Int,
    val rx: Int,
    val ry: Int,
    val holdMs: Long,
) {
    val isNeutral: Boolean get() = lx == 0 && ly == 0 && rx == 0 && ry == 0

    companion object {
        const val DEFAULT_HOLD_MS = 280L
        const val MIN_HOLD_MS = 50L
        const val MAX_HOLD_MS = 2000L

        /** Returns null for empty/invalid lines (wrong field count or non-numeric axes). */
        fun parse(line: String): StickCommand? {
            val parts = line.trim().split(Regex("\\s+")).filter { it.isNotEmpty() }
            val nums = parts.map { it.toLongOrNull() ?: return null }
            return when (nums.size) {
                2 -> StickCommand(nums[0].toInt(), nums[1].toInt(), 0, 0, DEFAULT_HOLD_MS)
                3 -> StickCommand(nums[0].toInt(), nums[1].toInt(), 0, 0, clampHold(nums[2]))
                5 -> StickCommand(
                    nums[0].toInt(), nums[1].toInt(), nums[2].toInt(), nums[3].toInt(), clampHold(nums[4]),
                )
                else -> null
            }
        }

        private fun clampHold(ms: Long) = ms.coerceIn(MIN_HOLD_MS, MAX_HOLD_MS)
    }
}

/**
 * Writes left/right stick axes to an evdev node and caches what was last sent, so unchanged
 * axes cost no `sendevent` process. The cache is bound to the node `path`: if the controller
 * reconnects and the node changes, the cache is dropped and the first write sends every axis
 * (otherwise an identical vector would be skipped and the new node would never receive it).
 *
 * Xbox node axes (getevent -lp on Odin 3): left stick ABS_X(0)/ABS_Y(1),
 * right stick ABS_Z(2)=yaw / ABS_RZ(5)=pitch. Pure Kotlin: `sendEvent` is injected for tests.
 */
class AxisWriter(
    private val sendEvent: (path: String, type: Int, code: Int, value: Int) -> Unit,
) {
    private var cachePath: String? = null
    private var sentLx = UNKNOWN
    private var sentLy = UNKNOWN
    private var sentRx = UNKNOWN
    private var sentRy = UNKNOWN

    /** Forget everything sent; the next [write] resends all axes. */
    @Synchronized
    fun invalidate() {
        cachePath = null
        sentLx = UNKNOWN
        sentLy = UNKNOWN
        sentRx = UNKNOWN
        sentRy = UNKNOWN
    }

    /**
     * @param force send every axis regardless of the cache (use for neutral/safety writes)
     * @return true on success; on failure the cache is invalidated (partial writes leave the
     *         node in an unknown state) and the exception is swallowed as `false`.
     */
    @Synchronized
    fun write(path: String, lx: Int, ly: Int, rx: Int, ry: Int, force: Boolean = false): Boolean {
        if (path != cachePath) {
            invalidate()
            cachePath = path
        }
        return try {
            var wrote = false
            if (force || lx != sentLx) { sendEvent(path, EV_ABS, ABS_X, lx); sentLx = lx; wrote = true }
            if (force || ly != sentLy) { sendEvent(path, EV_ABS, ABS_Y, ly); sentLy = ly; wrote = true }
            if (force || rx != sentRx) { sendEvent(path, EV_ABS, ABS_Z, rx); sentRx = rx; wrote = true }
            if (force || ry != sentRy) { sendEvent(path, EV_ABS, ABS_RZ, ry); sentRy = ry; wrote = true }
            if (wrote) sendEvent(path, EV_SYN, 0, 0)
            true
        } catch (e: Exception) {
            invalidate()
            false
        }
    }

    companion object {
        const val EV_SYN = 0
        const val EV_ABS = 3
        const val ABS_X = 0
        const val ABS_Y = 1
        const val ABS_Z = 2
        const val ABS_RZ = 5
        private const val UNKNOWN = Int.MIN_VALUE
    }
}
