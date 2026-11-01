package com.aliothmoon.maafw.remote.internal

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StickCommandTest {

    @Test
    fun `parses left only legacy three field line`() {
        val c = StickCommand.parse("0 -30000 600")!!
        assertEquals(StickCommand(0, -30000, 0, 0, 600), c)
        assertFalse(c.isNeutral)
    }

    @Test
    fun `parses five field line with camera`() {
        val c = StickCommand.parse("0 -30000 20000 0 300")!!
        assertEquals(StickCommand(0, -30000, 20000, 0, 300), c)
    }

    @Test
    fun `two field line uses default hold`() {
        assertEquals(StickCommand.DEFAULT_HOLD_MS, StickCommand.parse("1 2")!!.holdMs)
    }

    @Test
    fun `hold is clamped`() {
        assertEquals(StickCommand.MIN_HOLD_MS, StickCommand.parse("1 2 1")!!.holdMs)
        assertEquals(StickCommand.MAX_HOLD_MS, StickCommand.parse("1 2 0 0 99999")!!.holdMs)
    }

    @Test
    fun `invalid lines are rejected`() {
        assertNull(StickCommand.parse(""))
        assertNull(StickCommand.parse("1"))
        assertNull(StickCommand.parse("1 2 3 4"))        // 4 fields is ambiguous
        assertNull(StickCommand.parse("a b c"))
        assertNull(StickCommand.parse("1 2 3 4 5 6"))
    }

    @Test
    fun `neutral detection covers camera axes`() {
        assertTrue(StickCommand.parse("0 0 0 0 50")!!.isNeutral)
        assertFalse(StickCommand.parse("0 0 5000 0 50")!!.isNeutral)
    }
}

class AxisWriterTest {

    private data class Ev(val path: String, val type: Int, val code: Int, val value: Int)

    private class Rec(var failAt: Int = -1) {
        val events = mutableListOf<Ev>()
        fun send(path: String, type: Int, code: Int, value: Int) {
            if (failAt >= 0 && events.size == failAt) {
                failAt = -1
                throw IllegalStateException("boom")
            }
            events += Ev(path, type, code, value)
        }
    }

    private fun writer(rec: Rec) = AxisWriter(rec::send)

    @Test
    fun `first write sends every axis then SYN`() {
        val rec = Rec()
        assertTrue(writer(rec).write("/dev/input/event8", 0, -30000, 0, 0))
        assertEquals(
            listOf(
                Ev("/dev/input/event8", 3, AxisWriter.ABS_X, 0),
                Ev("/dev/input/event8", 3, AxisWriter.ABS_Y, -30000),
                Ev("/dev/input/event8", 3, AxisWriter.ABS_Z, 0),
                Ev("/dev/input/event8", 3, AxisWriter.ABS_RZ, 0),
                Ev("/dev/input/event8", 0, 0, 0),
            ),
            rec.events,
        )
    }

    @Test
    fun `identical vector on same node sends nothing`() {
        val rec = Rec()
        val w = writer(rec)
        w.write("/dev/input/event8", 1, 2, 3, 4)
        val n = rec.events.size
        assertTrue(w.write("/dev/input/event8", 1, 2, 3, 4))
        assertEquals(n, rec.events.size)
    }

    @Test
    fun `only changed axes are sent`() {
        val rec = Rec()
        val w = writer(rec)
        w.write("/dev/input/event8", 0, -30000, 0, 0)
        rec.events.clear()
        w.write("/dev/input/event8", 0, -30000, 20000, 0)
        assertEquals(
            listOf(Ev("/dev/input/event8", 3, AxisWriter.ABS_Z, 20000), Ev("/dev/input/event8", 0, 0, 0)),
            rec.events,
        )
    }

    /** Regression: controller reconnects (event8 → event9) and the same vector is requested. */
    @Test
    fun `node change invalidates cache and resends identical vector`() {
        val rec = Rec()
        val w = writer(rec)
        w.write("/dev/input/event8", 0, -30000, 0, 0)
        rec.events.clear()

        assertTrue(w.write("/dev/input/event9", 0, -30000, 0, 0))

        val axes = rec.events.filter { it.type == 3 }
        assertEquals(4, axes.size)
        assertTrue(rec.events.all { it.path == "/dev/input/event9" })
        assertEquals(Ev("/dev/input/event9", 0, 0, 0), rec.events.last())
    }

    @Test
    fun `node change then back also resends`() {
        val rec = Rec()
        val w = writer(rec)
        w.write("/dev/input/event8", 5, 5, 5, 5)
        w.write("/dev/input/event9", 5, 5, 5, 5)
        rec.events.clear()
        w.write("/dev/input/event8", 5, 5, 5, 5)
        assertEquals(5, rec.events.size) // 4 axes + SYN
    }

    @Test
    fun `failure mid write invalidates and next call resends everything`() {
        val rec = Rec(failAt = 2) // dies on the third event (rx)
        val w = writer(rec)
        assertFalse(w.write("/dev/input/event8", 1, 2, 3, 4))
        rec.events.clear()

        assertTrue(w.write("/dev/input/event8", 1, 2, 3, 4))
        assertEquals(5, rec.events.size)
    }

    @Test
    fun `force sends all axes even when unchanged`() {
        val rec = Rec()
        val w = writer(rec)
        w.write("/dev/input/event8", 0, 0, 0, 0)
        rec.events.clear()
        assertTrue(w.write("/dev/input/event8", 0, 0, 0, 0, force = true))
        assertEquals(5, rec.events.size)
    }

    @Test
    fun `invalidate forces resend`() {
        val rec = Rec()
        val w = writer(rec)
        w.write("/dev/input/event8", 7, 7, 7, 7)
        w.invalidate()
        rec.events.clear()
        w.write("/dev/input/event8", 7, 7, 7, 7)
        assertEquals(5, rec.events.size)
    }
}
