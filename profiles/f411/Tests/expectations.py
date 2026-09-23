"""Explicit MCU expectations; never inferred from the tested firmware."""
EXPECTED = {'clock': [('HSI', 'RCC->CFGR', 2, 3, 0),
           ('AHB', 'RCC->CFGR', 4, 15, 8),
           ('APB1', 'RCC->CFGR', 10, 7, 0),
           ('APB2', 'RCC->CFGR', 13, 7, 5)],
 'gpio': [('GPIOC clock', 'RCC->AHB1ENR', 2, 1, 1),
          ('PC13 output', 'GPIOC->MODER', 26, 3, 1),
          ('PC13 push-pull', 'GPIOC->OTYPER', 13, 1, 0),
          ('PC13 no pull', 'GPIOC->PUPDR', 26, 3, 0),
          ('PC13 low speed', 'GPIOC->OSPEEDR', 26, 3, 0),
          ('PC13 initial', 'GPIOC->ODR', 13, 1, 0)],
 'led_initial': 0,
 'gpio_mode_expression': '(GPIOC->MODER >> 26) & 3',
 'gpio_mode': 1,
 'dma_remaining': 'DMA2_Stream0->NDTR',
 'measurement_quality': 2}

EXPECTED["adc_vectors"] = [('*(unsigned short *)0x1FFF7A2C', '*(unsigned short *)0x1FFF7A2A', 3300, 30000), ('*(unsigned short *)0x1FFF7A2E', '*(unsigned short *)0x1FFF7A2A', 3300, 110000)]

EXPECTED.update(led_port="GPIOC", led_pin="GPIO_PIN_13", led_level="(GPIOC->ODR >> 13) & 1")
