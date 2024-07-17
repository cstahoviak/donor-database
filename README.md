# donor-database
A custom database for managing donors and payment information.

## Getting Started
A quick getting started guide.

1. Clone the `donor-database` repository locally.
    ```
    git clone https://github.com/cstahoviak/donor-database.git
    ```

2. (optional) Create and activate a virtual environment for the `donordatabase` 
package.
    ```
    mkdir pyvenv
    cd pyvenv
    python3 -m venv donor_database
    source pyvenv/donor_database/bin/activate 
    ```
   
3. Install the `donordatabase` package (as editable).
    ```
    cd donor-database
    python -m pip install --editable .
    ```
   
### Running the Analysis Script
Once the `donordatabase` package has been installed (either into the `base` 
environment or the `donor_database` environment), you can run the demo 
analysis script.
```
python emamples/database_analysis.py
```


