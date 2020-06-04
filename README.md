# ADS1230 

This library allows a raspberry pi to communicate with an ADS 1230 20 bit ADC, which is usually used in load cells or 
pressure sensors. Supported features right now are 
* trigger offset calibration
* pull measurements
* accidental standby protection
* direct conversion of measurements to units

For now the library expects the ADS1230 to be configured with the SPEED pin pulled to GND as the corresponsing timings
are hardcoded into the source.

## State of the project
At the moment the library does exactly what I need it to do. I've implemented the usecases I need while omitting several
features of the chip that I do not need. If you require additional functionality feel free to open an issue and I might 
add it. Also feel free to fork, I'll happily accept pull requests.

## Installing
I have not published this library to PyPi yet. For now you need to clone the repository and install it yourself.

This library depends on RPi.GPIO

## Usage

### In a loadcell/weight sensor

```python
from ads1230 import Loadcell

sensor = Loadcell(5,6)  # PIN_SCKL, PIN_DOUT
sensor.calibrate_zero()
# now place a reference weight on your sensor
sensor.calibrate_unit(1.0)  # the fraction indicates the ratio of your reference unit and your reference weight
# eg if you want to measure kilogram and your reference is 500g you need to use a fraction of 0.5

result = sensor.measure()
``` 

You can save the calibration by storing `sensor.unit_value` and restoring it upon restart. This way you won't need to 
calibrate the reference unit on every restart. You should however `sensor.calibrate_zero()` on every restart.

### Just the ADC
```python
from ads1230 import ADS1230
import time

ads = ADS1230(5,6)  # PIN_SCKL, PIN_DOUT
ads.calibrate()  # puts the device into calibration mode.
while not ads.is_ready():  # Wait until data is available
    time.sleep(0.1)
raw = ads.measure()  # read one measurement
``` 

## Notes on timing
The ADS1230 has some tight requirements on SCLK pulse timings. So far I've tested this only on a Raspberry PI 4 and I do
not know if previous models are able to act fast enough to prevent the ADS1230 from going into sleep mode. 
The library automatically measures the timing of the SCLK pulses and aborts a measurement with an 
`ADS1230TimingViolatedExcception` when violated. Even on a Raspberry PI 4 occasional appearances of this exception are
expected, for example when interrupted by a context switch.


