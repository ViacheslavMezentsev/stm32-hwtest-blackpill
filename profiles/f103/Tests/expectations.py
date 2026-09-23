"""Explicit MCU expectations; never inferred from the tested firmware."""
EXPECTED = {'clock': [('HSI', 'RCC->CFGR', 2, 3, 0),
           ('AHB', 'RCC->CFGR', 4, 15, 0),
           ('APB1', 'RCC->CFGR', 8, 7, 0),
           ('APB2', 'RCC->CFGR', 11, 7, 0)],
 'gpio': [('GPIOB clock', 'RCC->APB2ENR', 3, 1, 1),
          ('PB2 output 2 MHz', 'GPIOB->CRL', 8, 15, 2),
          ('PB2 initial', 'GPIOB->ODR', 2, 1, 1)],
 'led_initial': 1,
 'gpio_mode_expression': '(GPIOB->CRL >> 8) & 15',
 'gpio_mode': 2,
 'dma_remaining': 'DMA1_Channel1->CNDTR',
 'measurement_quality': 1}

EXPECTED["adc_vectors"] = [(1716, 1440, 3412, 25000), (2145, 1800, 2730, 25000), (1974, 1440, 3412, -25000), (1329, 1440, 3412, 100000)]

EXPECTED.update(led_port="GPIOB", led_pin="GPIO_PIN_2", led_level="(GPIOB->ODR >> 2) & 1")
