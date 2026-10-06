"""
RU: Запуск: отсутствие отказа, тактирование от HSI, вывод светодиода и профиль прогона платы.
EN: Startup: no fault, HSI clock, the LED pin and the run profile of the board.
"""
from stm32_gdbtest import case, one_of, within


# HSI is the system clock after reset, without the PLL (RM0383/RM0368: 16 MHz RC oscillator).
HSI_HZ = 16_000_000
# RCC_CFGR address (RCC base 0x40023800, offset 0x08). SWS (3:2), HPRE (7:4), PPRE1 (12:10) and
# PPRE2 (15:13) are zero for HSI as the system clock with undivided buses.
RCC_CFGR = 0x40023808
CFGR_CLOCK_FIELDS = 0xFCFC
# SRAM starts at 0x20000000; the stack is full descending, so the initial stack pointer may equal
# the end address: the first push stores below it (ld/stm32f4.ld.in).
SRAM_START = 0x20000000
# USART1 data register: a peripheral address, never read as memory.
USART1_DR = 0x40011004


# Verify that the application reaches loop() without a fault on the reset clock.
@case("HW_BOOT", labels=("boot",))
def boot(t):
    t.reach("loop")

    # program.cpp sees no device header, so the clock register is read at its address.
    t.check([
        ("no platform fault", "platform_fault", 0),
        ("core clock is HSI", "SystemCoreClock", HSI_HZ),
        ("HSI system clock, undivided buses",
         f"*(volatile unsigned int *)0x{RCC_CFGR:08X} & 0x{CFGR_CLOCK_FIELDS:04X}", 0)
    ])


# Verify the clock tree, the 1 ms SysTick and the electrical configuration of the LED pin.
@case("HW_CLOCK_GPIO_CONFIG", labels=("boot", "gpio"), contracts=("cmsis_clock_gpio",))
def clock_gpio_config(t):
    board = t.profile.data["board"]["board"]
    port, pin = board["led_port"], board["led_pin"]

    # TECH-001: the macros are visible in platform.c, the translation unit with the device header.
    t.reach("platform_led_toggle")

    # Reading SysTick->CTRL clears COUNTFLAG, which the application does not use: it counts interrupts.
    t.check([
        ("HSI on and ready", "RCC->CR & (RCC_CR_HSION | RCC_CR_HSIRDY)", "RCC_CR_HSION | RCC_CR_HSIRDY"),
        ("HSI system clock, undivided buses",
         "RCC->CFGR & (RCC_CFGR_SWS | RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2)", "RCC_CFGR_SWS_HSI"),
        ("core clock", "SystemCoreClock", HSI_HZ),
        ("SysTick period 1 ms", "SysTick->LOAD", HSI_HZ // 1000 - 1),
        ("SysTick core clock, interrupt, enabled",
         "SysTick->CTRL & (SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk)",
         "SysTick_CTRL_CLKSOURCE_Msk | SysTick_CTRL_TICKINT_Msk | SysTick_CTRL_ENABLE_Msk"),
        (f"{port} clock", f"RCC->AHB1ENR & RCC_AHB1ENR_{port}EN"),
        (f"P{port[-1]}{pin} output", f"{port}->MODER & GPIO_MODER_MODER{pin}", f"GPIO_MODER_MODER{pin}_0"),
        (f"P{port[-1]}{pin} push-pull", f"{port}->OTYPER & GPIO_OTYPER_OT{pin}", 0),
        (f"P{port[-1]}{pin} low speed", f"{port}->OSPEEDR & GPIO_OSPEEDER_OSPEEDR{pin}", 0),
        (f"P{port[-1]}{pin} no pull", f"{port}->PUPDR & GPIO_PUPDR_PUPDR{pin}", 0)
    ])


# Verify that the LED goes off, on and off again over three consecutive toggles.
@case("HW_GPIO", labels=("gpio",), contracts=("cmsis_clock_gpio",))
def gpio(t):
    board = t.profile.data["board"]["board"]
    led_on = (f"(({board['led_port']}->ODR & GPIO_ODR_OD{board['led_pin']}) != 0) == "
              f"{int(board['led_active_high'])}")

    # Each entry of platform_led_toggle() sees the level the previous toggle left.
    for expected in (0, 1, 0):
        t.reach("platform_led_toggle")
        t.check(f"LED {'on' if expected else 'off'} before the toggle", t.evaluate(led_on), expected)


# Verify that the image, the board data and the build belong to the board the run configuration names.
@case("HW_BOARD_PROFILE", labels=("boot", "profile"))
def board_profile(t):
    profile = t.profile
    board = profile.data["board"]["board"]

    # TECH-017: the MCU description, the board data and the build agree on the chip.
    t.check(f"{profile['mcu']} is a {board['name']}", board["name"] in profile["mcu"])
    t.check(f"the build defines {board['device']}", board["device"] in profile.build["defines"])
    t.check("the board data comes from its file", profile.origin("data.board.board.name")["file"],
            profile.files["data.board"]["reference"])
    t.check("the frame limit comes from api.toml", profile.origin("api.frames.limit")["state"], "file")

    # The chip answers as the description says: identity register and factory flash size.
    identity = profile["identity"]
    chip = t.evaluate(f"*(volatile unsigned int *)0x{identity['address']:08X}") & identity["mask"]
    t.check(f"DEV_ID 0x{chip:03X} matches {profile['mcu']}", chip, identity["value"])
    flash_kib = t.evaluate(f"*(volatile unsigned short *)0x{profile['flash_size_address']:08X}")
    t.check(f"F_SIZE {flash_kib} KiB covers the profile", flash_kib * 1024 >= profile["flash_size"])

    # The flashed image starts with a vector table: the stack in SRAM, reset in the flash, Thumb code.
    vectors = t.memory(profile["flash_start"], 8)
    stack, reset = int.from_bytes(vectors[:4], "little"), int.from_bytes(vectors[4:], "little")
    flash = within(profile["flash_start"], profile["flash_start"] + profile["flash_size"] - 1)
    t.check("initial stack pointer in SRAM", stack, within(SRAM_START + 8, SRAM_START + board["ram_kib"] * 1024))
    t.check("initial stack pointer 8-byte aligned (AAPCS)", stack % 8, 0)
    t.check("reset vector in the profile flash", reset & ~1, flash)
    t.check("reset vector is Thumb code", reset & 1)

    # TECH-012: a peripheral register is not read as memory, a read could change the device state.
    with t.refused("outside_window", name="USART1 data register is refused as memory"):
        t.memory(USART1_DR, 4)

    # The stand and GDB of this run are kept with the result.
    t.check("stand backend", profile.stand["backend"], one_of("openocd", "jlink", "stlink"))
    t.record("profile", profile)
