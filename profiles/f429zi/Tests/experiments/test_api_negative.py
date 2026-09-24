"""Deliberate failures, excluded from normal CTest collection (Tests/board only)."""

from stm32_gdbtest import case


@case("HW_BAD_FIELD")
def bad_field(t):
    t.reach("HAL_GPIO_Init", when="GPIOx == GPIOG")
    t.fields("*GPIO_Init", {"Mode": "GPIO_MODE_INPUT"})


@case("HW_FALSE_CONDITION")
def false_condition(t):
    t.reach("HAL_GPIO_TogglePin", when="0")


@case("HW_INVALID_CONDITION")
def invalid_condition(t):
    t.reach("HAL_GPIO_Init", when="missing_argument_xyz == 1")
