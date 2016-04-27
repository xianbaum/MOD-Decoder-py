#pymodinterpreter

Opens and interprets an MOD file.

##Dependencies

pymodinterpreter does not require anything to interpret the file. However, the print_pattern function requires tabulate to be installed.

To install tabulate, use:

```sh
pip install tabulate
```

##Setup

To use pymodinterperter, simply import it into your project.

##Usage

Use the 

```python
modobject = open_mod( pathtofile.mod ) 
``

function to open a file. It returns an interpreted object with the header data, the sample data and pattern data. Please refer to for all of the members inside of the MOD class for details.

##Support

pymodinterpreter opens MOD files only. However, it should be able to fully support opening any kind of MOD file. If there are any exceptions, please report it as a bug.
