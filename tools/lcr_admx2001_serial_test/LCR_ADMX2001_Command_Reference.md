# LCR ADMX2001 Command Reference

This document contains the complete help documentation for all commands of the LCR ADMX2001 instrument, collected via serial communication on COM4 at 115200 baud.

## Overview

The LCR ADMX2001 supports the following command categories:

- **MEASURE**: Commands for initiating and controlling measurements
- **MEASUREMENT CONFIGURATION**: Commands for setting measurement parameters
- **MEASUREMENT TIMING**: Commands for timing control
- **MULTIPOINT/SWEEP CONFIGURATION**: Commands for sweep and multipoint operations
- **COMPENSATION AND CALIBRATION**: Commands for calibration and compensation
- **UTILITY**: General utility commands

## Commands

### MEASURE

#### z
- **Command**: z - initiate measurement
- **Synopsis**: z
- **Description**: Measure impedance with the present settings. If sweep_type is given then it generates the number of samples as determined by the 'count' command. Additional information for 'z' command: display,tcount,count,offset,frequency, magnitude,setgain commands can impact the output

#### temperature
- **Command**: temperature - Display module temperature and set temperature unit.
- **Synopsis**: temperature [ <cls | fht> ]
- **Description**: Display current module temperature. Set display temperature unit to degree celsius (cls) or fahrenheit (fht). If no parameter is given then current module temperature is displayed.

#### initiate
- **Command**: initiate - Initializes the module for triggered measurement(s)
- **Synopsis**: initiate
- **Description**: Initializes the module for measurement. This command puts the module in the "WAIT_FOR_TRIGGER" state and disables certain commands.

#### trigger
- **Command**: trigger - Triggers the measurement
- **Synopsis**: trigger
- **Description**: Performs the measurement if the board is waiting for a trigger else, the trigger fails. If all triggers are completed, the state is set to IDLE.

#### abort
- **Command**: abort - Aborts the measurement
- **Synopsis**: abort
- **Description**: Aborts the measurement and sets the state to IDLE. All disabled commands are enabled after the abort command.

### MEASUREMENT CONFIGURATION

#### frequency
- **Command**: frequency - sets frequency of the test signal
- **Synopsis**: frequency [ <frequency> ]
- **Description**: Sets the test signal to <frequency>, where <frequency> is a floating point number in kHz. Valid input range is between 0.0kHz and 10.0MHz.

#### magnitude
- **Command**: magnitude - sets the magnitude of the test signal
- **Synopsis**: magnitude [ <magnitude> ]
- **Description**: Sets the test signal <magnitude>, where <magnitude> is a floating point number representing peak output voltage. Valid input range is between 0.0 and 2.25

#### offset
- **Command**: offset - sets dc bias (offset) of the test signal
- **Synopsis**: offset [ <offset> ]
- **Description**: Sets the test signal's dc bias to <offset>, where <offset> is a floating point number representing dc bias voltage. Valid input range is between -2.5 and +2.5

#### setgain
- **Command**: setgain - display (or set) voltage and current measurement channel gain (measurement range)
- **Synopsis**: setgain [ <auto> | [ <ch0 | ch1> [ <gain> ] ] ]
- **Description**: <auto> enables the autorange functionality for both the current and voltage gain settings. Set the voltage measurement channel gain (ch0) or current measurement channel gain (ch1). Voltage measurement channel gain options are 0,1,2,3 which correspond to 1,2,4,8 (V/V) respectively. Current measurement channel gain options are 0,1,2,3 which correspond to 100, 1k, 10k, 100k (Ohm) respectively. If no parameters are given then presently set gain setting(s) is reported.

**Detailed Gain Settings:**
- **Voltage Channel (ch0)**: Gain values 0,1,2,3 correspond to amplification factors of 1×, 2×, 4×, 8× (V/V)
- **Current Channel (ch1)**: Gain values 0,1,2,3 correspond to measurement ranges of 100Ω, 1kΩ, 10kΩ, 100kΩ
- **Auto Mode**: Enables automatic ranging for both voltage and current channels

#### trig_mode
- **Command**: trig_mode - Sets trigger mode
- **Synopsis**: trig_mode [ <internal> <external> ]
- **Description**: Set the trigger mode to internal or external. trig_mode internal - Does immediate measurement. trig_mode external - Waits for external trigger & then measures. If no parameter is given then the current state is displayed.

#### average
- **Command**: average - set or display the sample average
- **Synopsis**: average [ <n> ]
- **Description**: Set the sample average for impedance (admittance) measurements to <n> where <n> is an integer with range [1, 65536]. If no parameter is given then the sample average setting is reported.

#### display
- **Command**: display - set or display measurement model
- **Synopsis**: display [ <model number> ]
- **Description**: Set the measurement model number:
  - 0 - Equivalent series capacitance and resistance (Cs,Rs)
  - 1 - Equivalent series capacitance and dissipation factor (Cs,D)
  - 2 - Equivalent series capacitance and quality factor (Cs,Q)
  - 3 - Inductance and equivalent series resistance (Ls,Rs)
  - 4 - Equivalent series inductance and dissipation factor (Ls,D)
  - 5 - Equivalent series inductance and quality factor (Ls,Q)
  - 6 - Impedance in rectangular coordinates (default) (R,X)
  - 7 - Impedance in magnitude and phase in degrees (Z,deg)
  - 8 - Impedance in magnitude and phase in radians (Z,rad)
  - 9 - Capacitance and equivalent parallel resistance (Cp,Rp)
  - 10 - Equivalent parallel capacitance and dissipation factor (Cp,D)
  - 11 - Equivalent parallel capacitance and quality factor (Cp,Q)
  - 12 - Inductance and equivalent parallel resistance (Lp,Rp)
  - 13 - Equivalent parallel inductance and dissipation factor (Lp,D)
  - 14 - Equivalent parallel inductance and quality factor (Lp,Q)
  - 15 - Admittance in rectangular coordinates (G,B)
  - 16 - Admittance in magnitude and phase in degrees (Y,deg)
  - 17 - Admittance in magnitude and phase in radians (Y,rad)
  - 18 - off

  If no parameter is given then the LCR reports presently set model number.

### MEASUREMENT TIMING

#### mdelay
- **Command**: mdelay - set or display the measurement delay in milliseconds
- **Synopsis**: mdelay [ <time (msec)> ]
- **Description**: Set the delay between the measurements selected by the 'count' command to <n> where <n> is an integer with range [0, 82000]. If no parameter is given then the measurement delay setting is reported. Use this delay to allow sufficient settling time between readings in a sweep.

#### tdelay
- **Command**: tdelay - set or display the trigger delay in milliseconds
- **Synopsis**: tdelay [ <time (msec)> ]
- **Description**: Set the trigger delay between measurement cycles selected by the 'tcount' command to <n> where <n> is an integer with range [0, 65536]. If no parameter is given then the trigger delay setting is reported.

### MULTIPOINT/SWEEP CONFIGURATION

#### count
- **Command**: count - set or display the sample count
- **Synopsis**: count [ <n> ]
- **Description**: Set the sample count for impedance (admittance) measurements to <n> where <n> is an integer with range [1, 255]. If no parameters is given then the sample count setting is reported.

#### tcount
- **Command**: tcount - set or display the trigger count
- **Synopsis**: tcount [ <n> ]
- **Description**: Set the trigger count to <n> where <n> is an integer with range = [1, 65536]. The trigger count value determines how many times the measurement cycle set by the 'count' command is repeated. If no parameter is given then the tcount setting is reported.

#### sweep_type
- **Command**: sweep_type - set the sweep type and range
- **Synopsis**: sweep_type [<frequency | magnitude | offset | off> [<Sweep Start> <Sweep End>]]
- **Description**: Sets the Sweep Type to be a sweep on frequency, ac magnitude, or dc bias (offset) of the test signal. <Sweep Start> and <Sweep End> determine the first and last point of the sweep. Can be ignored for 'off' option. The number of points in the sweep is set by the 'count' command. If no parameter is given then the sweep parameter is reported.

**Sweep Types:**
- **frequency**: Sweep test signal frequency from <Sweep Start> to <Sweep End> (in kHz)
- **magnitude**: Sweep AC test signal magnitude from <Sweep Start> to <Sweep End> (in volts)
- **offset**: Sweep DC bias (offset) from <Sweep Start> to <Sweep End> (in volts)
- **off**: Disable sweeping (single point measurement mode)

**Measurement Process**: When sweep_type is set and 'z' command is executed, it generates the number of samples determined by the 'count' command, with each sample taken at a different sweep parameter value.

#### sweep_scale
- **Command**: sweep_scale - set the sweep scale
- **Synopsis**: sweep_scale [<linear|log>]
- **Description**: Set the scale for the sweep loop. Decides the type of increments between the limit values of the sweep decided by the range. If no parameter is given then the sweep_scale setting is reported.

**Scale Types:**
- **linear**: Linear increments between sweep start and end values
- **log**: Logarithmic increments between sweep start and end values (useful for frequency sweeps)

**Usage**: The sweep_scale setting affects how the sweep parameter values are distributed between the start and end points set by sweep_type.

### COMPENSATION AND CALIBRATION

#### compensation
- **Command**: compensation - executes fixture compensation routines or displays the present compensation settings
- **Synopsis**: compensation [ <on | off | reset | open | short | rt <rt_value> | xt <xt_value> ] > ]
- **Description**: This command will execute the following compensation routines depending on the parameter given:
  - 'compensation on' - enables the application of compensation correction coefficients to the readings returned by the module
  - 'compensation off' - disables the application of compensation correction coefficients to the readings returned by the module
  - 'compensation reset' - resets the compensation coefficients
  - 'compensation open' - runs the open compensation routine
  - 'compensation short' - runs short compensation routine
  - 'compensation rt <rt_value> xt <xt_value>' - runs the load compensation routine using <rt_value> and <xt_value> as the true resistance and reactance values of the device under test
  - 'compensation' - if no parameter is given then the current compensation settings are displayed

#### rdcomp
- **Command**: rdcomp - Display compensation coefficients available in memory.
- **Synopsis**: rdcomp
- **Description**: This command displays compensation coefficients available in memory

#### storecomp
- **Command**: storecomp - Load user-defined compensation coefficients <value> to memory
- **Synopsis**: storecomp [ <coefficient> <value> ]
- **Description**: This command writes an individual compensation coefficient <value> to memory. Individual <coefficient> list: Ro, Xo, Go, Bo, Rs, Xs, Gs, Bs, Rg, Xg, Gg, Bg

#### calibrate
- **Command**: calibrate - executes calibration routines or displays the present calibration status
- **Synopsis**: calibrate [ <on | off | open | short | reload | rt [ xt ] | commit [ timestamp ] | erase | list | switch [evalkit / default] | passwd > ]
- **Description**: This command will execute the following routines depending on the parameter given:
  - 'calibrate' - displays calibration status, including time and temperature of the last commit
  - 'calibrate open' - runs the open calibration routine on the presently selected measurement range
  - 'calibrate short' - runs the short calibration routine on the presently selected measurement range
  - 'calibrate rt <rt_value> xt <xt_value>' - runs the load calibration routine using <rt_value> and <xt_value> as the true resistance and reactance values of the device under test
  - 'calibrate on' - enables the application of calibration coefficients to the readings returned by the module (default mode)
  - 'calibrate off' - disables the application of calibration and compensation coefficients
  - 'calibrate reload' will reload calibration coefficients from flash memory to the RAM
  - 'calibrate commit' - stores all calibration coefficients in the RAM into the flash memory
  - 'calibrate commit <unix epoch time in seconds>' - stores all calibration coefficients in the RAM into the flash memory and sets the date and time
  - 'calibrate erase' - Erase the calibration coefficients stored in flash memory.
  - 'calibrate list <freq>' - list the frequency os calibration coefficients stored in flash memory.
  - 'calibrate switch <evalkit / default>' - used to switch between evalkit | user coefficients sets stored in flash memory.
  - 'calibrate passwd' - change cal commit password to a new one. Maximum password length is 12 characters. Characters beyond this length will be ignored

  Additional information for calibrate command: setgain, offset, frequency, magnitude, tdelay, mdelay, and average commands can impact the calibration coefficients derived. The load calibration routine should be executed after open and short calibration (when applicable)

**Calibration Workflow:**
1. **Preparation**: Set measurement parameters (frequency, magnitude, offset, setgain, etc.)
2. **Open Calibration**: `calibrate open` - Measure open circuit
3. **Short Calibration**: `calibrate short` - Measure short circuit  
4. **Load Calibration** (optional): `calibrate rt <rt> xt <xt>` - Measure known load
5. **Commit**: `calibrate commit` - Save coefficients to flash memory
6. **Enable**: `calibrate on` - Apply calibration to measurements

**Calibration Status Query**: Use `calibrate` (no parameters) to check current status and last commit time/temperature.

#### rdcal
- **Command**: rdcal - Display calibration coefficients loaded in memory.
- **Synopsis**: rdcal [ <vgain> <igain> ]
- **Description**: This command displays calibration coefficients for the selected <vgain igain> combination (measurement range) available in memory. Valid range for <vgain> and <igain> is 0 to 3 for AC and DC calibration coefficients. <vgain> and <igain> for the present measurement range can be found with the 'setgain' command.

#### resetcal
- **Command**: resetcal - Reset the calibration coefficients in the memory, based on the measurement mode selected (AC or DC)
- **Synopsis**: resetcal [ <vgain> <igain>]
- **Description**: This command resets calibration coefficients for the given <vgain> and <igain> to defaults. Valid range for <vgain> and <igain> is 0 to 3 for AC and DCcalibration coefficients. If no <vgain> and <igain> arguments are provided, the command resets all the coefficients available in memory for the measurement mode presently set

#### storecal
- **Command**: storecal - Write individual calibration coefficients to RAM
- **Synopsis**: storecal [ <vgain> <igain> <coefficient> <value> ]
- **Description**: This command assigns <value> to individual calibration coefficients to the RAM without running the calibration routines. The coefficients are selected by the respective <vgain> and <igain> as defined by the 'setgain' command. Individual <coefficient> list: Ro, Xo, Go, Bo, Rs, Xs, Gs, Bs, Rg, Xg, Gg, Bg, Rdg, Rdo

### UTILITY

#### *idn?
- **Command**: *idn? - (SCPI standard identification query)
- **Synopsis**: *idn?
- **Description**: Returns the instrument identification string

#### help
- **Command**: help - Display command information
- **Synopsis**: help [ <command> ]
- **Description**: To display command information, type 'help' followed by any command listed below.

#### get_attr
- **Command**: get_attr - Prints attributes value
- **Synopsis**: get_attr
- **Description**: Fetches and displays attributes value.

#### error_check
- **Command**: error_check - Enable (on) or Disable (off) ADC overflow/FIFO error check
- **Synopsis**: error_check [ <on | off> ]
- **Description**: Enable (on) or Disable (off) ADC overflow/FIFO error check (on). If enabled impedance values are not returned on error Instead error message is displayed. If no parameter is given then the current state is displayed.

#### cls
- **Command**: cls - Clear screen/status
- **Synopsis**: cls
- **Description**: Clears the instrument's display or status

#### history
- **Command**: history - show command history
- **Synopsis**: history
- **Description**: Display command line help history.

#### reset
- **Command**: reset - Reset module state
- **Synopsis**: reset
- **Description**: This command resets the module state to default

#### selftest
- **Command**: selftest - Self test status
- **Synopsis**: selftest [ <run> ]
- **Description**: Prints self test status. run - Re-runs the self test. INFO : Open the test leads before running self-test

#### gpio_ctrl
- **Command**: gpio_ctrl - Control GPIO'S 1 -> Turn On 0 -> Turn Off
- **Synopsis**: gpio_ctrl [ <n> ]
- **Description**: where [ <n> ] ranges from [0 to 255]. Total of 8 GPIO'S are supported, all the GPIO'S are output enabled. Each GPIO is control by 1 bit in the argument.

## Communication Protocol and Data Formats

This section documents the actual communication behavior observed during testing with the instrument.

### Response Format Pattern

All commands follow a consistent response pattern:
1. **Command Echo**: The instrument echoes back the received command
2. **Response Data**: The actual result or confirmation data
3. **Prompt**: Ends with `ADMX2001>` prompt

Example:
```
[SEND] 'frequency 1000\r\n'
[RECV]
  frequency 1000
  frequency = 1000.0000kHz
ADMX2001>
```

### Measurement Data Format

The `z` (measure) command returns data in different formats depending on the measurement mode:

**For single point measurement (sweep_type off):**
```
index,Rs,Xs
index,Rs,Xs
...
```
- `index`: Sample index (0-based, integer)
- `Rs`: Series resistance (float, scientific notation)
- `Xs`: Series reactance (float, scientific notation)
- Number of lines equals the `count` parameter value

Example:
```
0,-2.229567e+03,-5.325690e+04
1,-2.219107e+03,-5.327530e+04
2,-2.227981e+03,-5.329631e+04
```

**For sweep mode (sweep_type set to frequency/magnitude/offset):**
```
frequency,Rs,Xs
frequency,Rs,Xs
...
```
- `frequency`: Current sweep frequency in Hz (float)
- `Rs`: Series resistance (float, scientific notation)
- `Xs`: Series reactance (float, scientific notation)
- Number of lines equals the `count` parameter value
- Frequencies are distributed according to `sweep_scale` (linear/log) between start and end values

Example (frequency sweep from 1000kHz to 2000kHz, linear, 3 points):
```
1.000000e+06,-2.215082e+03,-5.342812e+04
1.500000e+06,8.421753e+03,-3.900246e+04
2.000000e+06,1.155879e+04,-3.231040e+04
```

### Configuration Query Response

The `get_attr` command provides a comprehensive status report:

```
Measurement settings:
frequency = 1000.0000kHz
ac magnitude = 1.0000V
dc level = 0.0000V
measurement display mode = Impedance in rectangular coordinates (default) (Rs,Xs)
voltage gain = [gain_index, gain_value]
current gain = [gain_index, gain_value]
average = 10
compensation is off
auto range is on
Measurement timing:
sample count = 5
measurement delay = 1.0000msec
trigger count = 1
trigger delay = 4.0000msec
Multipoint measurement settings:
sweep type is off
sweep scale is linear
```

### Setting Command Confirmations

Configuration commands confirm the new setting:

- **Frequency**: `frequency = 1000.0000kHz`
- **Magnitude**: `magnitude = 1.0000`
- **Offset**: `Offset = 0.0000`
- **Average**: `average = 10`
- **Count**: `sampleCount = 5`
- **Display**: `Measurement model: 6 - Impedance in rectangular coordinates (default) (Rs,Xs)`
- **Trigger Mode**: `Trigger mode is internal`
- **Setgain**: `Autorange enabled`
- **Error Check**: `Error check is on`

### Instrument Status Information

- **Identification**: `*idn?` returns firmware version, build date, and board ID
- **Temperature**: `Current Temperature = 41.875000 deg C`
- **Calibration**: Reset command shows "1 number of entries found in calibration table"

### Driver Development Considerations

1. **Response Parsing**: Skip command echo, extract data after echo
2. **Data Types**: Measurement results are floats, indices are integers
3. **State Management**: Use `get_attr` for complete configuration snapshots
4. **Parameter Validation**: Commands confirm valid settings with formatted output
5. **Error Handling**: Enable `error_check` for ADC overflow detection
6. **Timing**: Allow sufficient delay between commands for processing
7. **Gain Settings**: 
   - Voltage gains: 0=1×, 1=2×, 2=4×, 3=8× (V/V)
   - Current gains: 0=100Ω, 1=1kΩ, 2=10kΩ, 3=100kΩ range
   - Use auto mode for automatic ranging
8. **Calibration Management**: 
   - Calibration affects measurement accuracy significantly
   - Workflow: set parameters → open cal → short cal → load cal (optional) → commit → enable
   - Use 'calibrate' (no params) to check status and last commit time/temperature
   - Calibration coefficients are stored in flash memory and can be reloaded with 'calibrate reload'
   - Multiple calibration sets can be stored (evalkit/default) and switched with 'calibrate switch'
   - Password protection available for commit operations

### Special Protocol Requirements

#### Line Ending Requirements

**Standard Commands** (frequency, magnitude, temperature, etc.):
- **Accepted endings**: `\r\n`, `\r`, `\n`
- **Recommended**: `\r\n` (standard CRLF)
- **Compatibility**: All three line endings work correctly

**Calibration Commit Command** (special case):
- **Command Line Ending**: Must use `\r` (carriage return only) instead of `\r\n`
- **Password Input**: When prompted with `PASSWORD>`, input must use `\n` (newline only)
- **Sequence**: 
  1. Send `calibrate commit\r`
  2. Wait for `PASSWORD>` prompt
  3. Send password followed by `\n` (e.g., `Analog123\n`)

**Example Implementation:**
```python
# Send calibrate commit command with \r only
ser.write(b'calibrate commit\r')
# Wait for PASSWORD> prompt
response = read_response()
if 'PASSWORD>' in response:
    # Send password with \n only
    ser.write(b'Analog123\n')
```

This special handling is required for successful calibration coefficient storage to flash memory.

#### ANSI Escape Sequence Filtering
All instrument responses contain ANSI escape sequences for terminal formatting. These must be stripped for clean data parsing:

- **Common Sequences**: `\x1b[0m`, `\x1b[1m`, `\x1b[2J`, etc.
- **Implementation**: Use regex or string replacement to remove escape sequences before parsing measurement data

#### Response Timing
- **Command Processing**: Allow 100-500ms delay after sending commands before reading response
- **Measurement Operations**: `z` command may take several seconds for sweep operations with high sample counts
- **Calibration Operations**: Open/short calibration routines require 2-5 seconds each

### Command Categories Summary

| Category | Commands | Purpose |
|----------|----------|---------|
| **MEASURE** | z, temperature, initiate, trigger, abort | Measurement execution and control |
| **CONFIG** | frequency, magnitude, offset, setgain, trig_mode, average, display | Measurement parameter settings |
| **TIMING** | mdelay, tdelay, count, tcount | Timing and sample control |
| **SWEEP** | sweep_type, sweep_scale | Multipoint measurement configuration |
| **CALIBRATION** | calibrate, compensation, rdcal, rdcomp, storecal, storecomp, resetcal | Accuracy calibration and compensation |
| **UTILITY** | *idn?, help, get_attr, error_check, cls, history, reset, selftest, gpio_ctrl | System information and control |