"""Офлайн-проверки MMIO: права, эффекты, частичная установка и очистка."""
import ast
import importlib.util
from pathlib import Path
import sys
import tomllib
from unittest.mock import Mock, patch
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules/stm32-gdbtest"))
from stm32_gdbtest.mmio import MMIO, MMIOError
from stm32_gdbtest.records import Journal
from stm32_gdbtest.svd import parse


def scenario(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "hil/common/tests/board" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Tests(unittest.TestCase):
    def setUp(self):
        self.catalog = parse((ROOT / "hil/common/stm32f4-test.svd").read_bytes())
        self.transport = Mock()
        self.transport.read.return_value = b"\x01\x00\x00\x00"
        self.transport.write.return_value = None
        self.mmio = MMIO(self.catalog, self.transport, Journal().record)

    def test_rights_and_effects_fail_before_transport(self):
        for name in ("SysTick.CTRL", "ADC1.DR", "NVIC.ICER0", "DMA2.LIFCR"):
            with self.subTest(name=name), self.assertRaises(MMIOError):
                self.mmio.read(name)
        for name in ("NVIC.ISER0", "NVIC.ICER1", "SCB.ICSR", "DMA2_Stream0.CR", "ADC1.CR2",
                     "DMA2.LIFCR", "TIM2.SR", "FACTORY.VREFINT_CAL"):
            with self.subTest(name=name), self.assertRaises(MMIOError):
                self.mmio.write(name, 0)
        self.transport.prepare.assert_not_called()

    def test_w1c_one_write_no_read(self):
        self.mmio.write("NVIC.ICER1", 1 << 24, allow_effects=True)
        self.transport.write.assert_called_once()
        self.transport.read.assert_not_called()
        self.assertEqual(self.transport.write.call_args.args[-2:], (0xE000E184, b"\x00\x00\x00\x01"))

    def test_factory_values_use_halfword(self):
        self.transport.read.return_value = b"\x34\x12"
        for name in ("FLASH_SIZE", "VREFINT_CAL", "TS_CAL1", "TS_CAL2"):
            self.assertEqual(self.mmio.read("FACTORY." + name), 0x1234)
            self.assertEqual(self.transport.read.call_args.args[-1], 2)

    def test_profiles_and_independent_factory_addresses(self):
        for board in ("F401CC", "F411CE"):
            folder = ROOT / "hil" / board
            target = tomllib.loads((folder / "target.toml").read_text(encoding="utf-8"))
            data = tomllib.loads((folder / "board.toml").read_text(encoding="utf-8"))["adc"]
            self.assertEqual(self.catalog.registers["DBGMCU.IDCODE"].address, target["identity"]["address"])
            self.assertEqual(self.catalog.registers["FACTORY.FLASH_SIZE"].address, target["flash_size_address"])
            for name, key, address in (("VREFINT_CAL", "vrefint_cal_address", 0x1FFF7A2A),
                                      ("TS_CAL1", "ts_cal1_address", 0x1FFF7A2C),
                                      ("TS_CAL2", "ts_cal2_address", 0x1FFF7A2E)):
                self.assertEqual(self.catalog.registers["FACTORY." + name].address, address)
                self.assertEqual(data[key], address)

    def target(self):
        t = Mock()
        t.profile.get.return_value = 100
        t.read.return_value = 0
        values = {
            "SCB_SCR_SLEEPONEXIT_Msk | SCB_SCR_SLEEPDEEP_Msk": 6,
            "1 << TIM2_IRQn": 1 << 28, "SCB_ICSR_PENDSTCLR_Msk": 1 << 25,
            "DMA2_Stream0_IRQn >> 5": 1, "1 << (DMA2_Stream0_IRQn & 31)": 1 << 24,
            "ADC_CR2_ADON": 1, "DMA_SxCR_EN": 1, "(unsigned int)samples": 0x20001000
        }
        t.evaluate.side_effect = values.__getitem__
        state = {"SCB.SCR": 0, "SysTick.CTRL": 0x10007, "NVIC.ISER0": 0x10000080,
                 "NVIC.ISER1": 0x01000040, "ADC1.CR2": 0x301, "DMA2_Stream0.CR": 0x400,
                 "DMA2_Stream0.NDTR": 0, "DMA2_Stream0.M0AR": 0x20000010}
        t.mmio.read.side_effect = lambda name, **kwargs: state[name]
        writes = []
        def write(name, value, **kwargs):
            writes.append((name, value, kwargs))
            if name.startswith("NVIC.ICER"):
                state[name.replace("ICER", "ISER")] &= ~value
            elif name.startswith("NVIC.ISER"):
                state[name] |= value
            else:
                state[name] = value
        t.mmio.write.side_effect = write
        return t, state, writes, write

    def test_sleep_partial_install_and_observation_failure_restore(self):
        m = scenario("test_sleep")
        for function in (m.sleep_systick, m.sleep_tim2):
            for fail_at in (1, 2, 3, 4, None):
                t, state, writes, write = self.target()
                def failing(name, value, **kw):
                    write(name, value, **kw)
                    if len(writes) == fail_at:
                        raise RuntimeError("lost ACK")
                t.mmio.write.side_effect = failing
                with patch.object(m, "reach_wfi_irq", side_effect=RuntimeError("observation failed")):
                    with self.assertRaises(RuntimeError):
                        function(t)
                self.assertEqual(state["NVIC.ISER0"], 0x10000080)
                self.assertEqual(state["NVIC.ISER1"], 0x01000040)
                if function == m.sleep_tim2:
                    self.assertEqual(state["SysTick.CTRL"], 7)
                self.assertTrue(all(v == 1 << 25 for n, v, _ in writes if n == "SCB.ICSR"))

    def test_restore_attempts_second_bank_if_first_fails(self):
        m = scenario("test_sleep")
        t = Mock()
        t.mmio.write.side_effect = [RuntimeError("restore bank0"), None]
        with self.assertRaises(RuntimeError):
            m.restore_irqs(t, [3, 4])
        self.assertEqual(t.mmio.write.call_count, 2)
        self.assertEqual(t.mmio.write.call_args.args, ("NVIC.ISER1", 4))

    def test_adc_timeout_preserves_prior_irq_state(self):
        for name, function in (("test_adc_faults", "adc_timeout"),
                               ("test_ddtt_feedback", "adc_timeout_diagnostic")):
            for initially_enabled in (True, False):
                t, state, writes, _ = self.target()
                if not initially_enabled:
                    state["NVIC.ISER1"] &= ~(1 << 24)
                saved = state["NVIC.ISER1"]
                t.reach.side_effect = [None, RuntimeError("observation failed")]
                with self.assertRaises(RuntimeError):
                    getattr(scenario(name), function)(t)
                self.assertEqual(state["NVIC.ISER1"], saved)
                self.assertEqual(sum(n == "NVIC.ISER1" for n, _, _ in writes), int(initially_enabled))

    def test_adc_disable_exception_restores_bit(self):
        t, state, writes, _ = self.target()
        t.reach.side_effect = [None, RuntimeError("no error stop")]
        with self.assertRaises(RuntimeError):
            scenario("test_adc_faults").adc_disabled(t)
        self.assertEqual(state["ADC1.CR2"], 0x301)
        self.assertEqual([v for n, v, _ in writes], [0x300, 0x301])

    def test_dma_partial_install_restores_snapshot(self):
        for fail_at in (1, 2, 3, None):
            t, state, writes, write = self.target()
            saved = {k: v for k, v in state.items() if k.startswith("DMA2_Stream0")}
            def failing(name, value, **kw):
                write(name, value, **kw)
                if len(writes) == fail_at:
                    raise RuntimeError("lost ACK")
            t.mmio.write.side_effect = failing
            t.reach.side_effect = [None, RuntimeError("no error stop")]
            with self.assertRaises(RuntimeError):
                scenario("test_adc_faults").adc_busy(t)
            self.assertEqual({k: state[k] for k in saved}, saved)

    def test_dma_disable_timeout_does_not_write_running_count(self):
        t, state, writes, write = self.target()
        def stuck(name, value, **kw):
            if name == "DMA2_Stream0.CR" and not value & 1 and state[name] & 1:
                writes.append((name, value, kw))
                return
            write(name, value, **kw)
        t.mmio.write.side_effect = stuck
        with self.assertRaisesRegex(RuntimeError, "restoration refused"):
            scenario("test_adc_faults").adc_busy(t)
        self.assertEqual(sum(n == "DMA2_Stream0.NDTR" for n, _, _ in writes), 1)
        self.assertEqual(sum(n == "DMA2_Stream0.M0AR" for n, _, _ in writes), 1)

    def test_dma_busy_preflight_writes_nothing(self):
        t, state, writes, _ = self.target()
        state["DMA2_Stream0.CR"] |= 1
        with self.assertRaisesRegex(RuntimeError, "must be disabled"):
            scenario("test_adc_faults").adc_busy(t)
        self.assertEqual(writes, [])

    def test_no_legacy_peripheral_dereference(self):
        for path in (ROOT / "hil/common/tests/board").glob("test_*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue
                if ast.unparse(node.func) not in ("t.read", "t.evaluate", "t.write", "t.check"):
                    continue
                args = node.args if node.func.attr != "check" else []
                if node.func.attr == "check" and node.args and isinstance(node.args[0], ast.List):
                    args = [v for row in node.args[0].elts for v in row.elts[1:]]
                for arg in args:
                    for part in ast.walk(arg):
                        if isinstance(part, ast.Constant) and isinstance(part.value, str):
                            if "->" in part.value:
                                self.assertIn("&ADC1->DR", part.value, path.name)
                            self.assertNotIn("volatile unsigned", part.value, path.name)


if __name__ == "__main__":
    unittest.main()

