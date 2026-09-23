"""Explicit MCU expectations; never inferred from the tested firmware."""
EXPECTED = {'clock': [('HSI', 'RCC->CFGR', 2, 3, 0),
           ('AHB', 'RCC->CFGR', 4, 15, 0),
           ('APB1', 'RCC->CFGR', 8, 7, 0),
           ('APB2', 'RCC->CFGR', 11, 7, 0)],
 'gpio': [('GPIOC clock', 'RCC->APB2ENR', 4, 1, 1),
          ('PC13 output 2 MHz', 'GPIOC->CRH', 20, 15, 2),
          ('PC13 initial', 'GPIOC->ODR', 13, 1, 1)],
 'led_initial': 1,
 'gpio_mode_expression': '(GPIOC->CRH >> 20) & 15',
 'gpio_mode': 2,
 'dma_remaining': 'DMA1_Channel1->CNDTR',
 'measurement_quality': 1}

EXPECTED["adc_vectors"] = [(1716, 1440, 3412, 25000), (2145, 1800, 2730, 25000), (1974, 1440, 3412, -25000), (1329, 1440, 3412, 100000)]
