"""Target API. Imported only inside GDB's main Python thread."""

import gdb


class CheckFailed(AssertionError):
    pass


class Target:
    def __init__(self, report):
        self.report = report
        self.owned = []
        self.stops = []
        gdb.events.stop.connect(self.on_stop)

    def on_stop(self, event):
        # Capture primitive values now: temporary breakpoint objects expire after stop.
        self.stops.append({"type": type(event).__name__,
                           "breakpoints": [bp.number for bp in getattr(event, "breakpoints", ())],
                           "signal": getattr(event, "stop_signal", None)})

    def check(self, name, actual, expected):
        passed = actual == expected
        self.report["checks"].append(dict(name=name, actual=actual, expected=expected, passed=passed))
        print(f"{'PASS' if passed else 'FAIL'} {name}: {actual!r}, expected {expected!r}")
        if not passed:
            raise CheckFailed(name)

    def value(self, expression):
        value = gdb.parse_and_eval(expression)
        if value.is_optimized_out:
            raise RuntimeError(f"Value optimized out: {expression}")
        value.fetch_lazy()
        return int(value)

    def breakpoint(self, function, temporary=False):
        if sum(bp.is_valid() for bp in self.owned) >= 6:
            raise RuntimeError("F411 hardware breakpoint budget exhausted")
        bp = gdb.Breakpoint(function, type=gdb.BP_HARDWARE_BREAKPOINT, temporary=temporary)
        self.owned.append(bp)
        return bp

    def reach(self, function):
        bp = self.breakpoint(function, temporary=True)
        number = bp.number
        self.stops.clear()
        try:
            gdb.execute("continue")
            stop = self.stops[-1] if self.stops else {}
            self.report.setdefault("stops", []).append(stop)
            self.check(f"breakpoint reached: {function}", number in stop.get("breakpoints", []), True)
            self.check(f"frame: {function}", gdb.newest_frame().name(), function)
        finally:
            if bp.is_valid():
                bp.delete()

    def boot(self, reset_command):
        self.clear()
        gdb.execute(reset_command)
        for name in ("HardFault_Handler", "MemManage_Handler", "BusFault_Handler", "UsageFault_Handler"):
            self.breakpoint(name)
        self.reach("main")

    def force_return(self, expression):
        gdb.execute("return " + expression)

    def clear(self):
        for bp in self.owned:
            if bp.is_valid():
                bp.delete()
        self.owned.clear()

    def close(self):
        gdb.events.stop.disconnect(self.on_stop)
        self.clear()
