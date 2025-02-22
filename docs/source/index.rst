.. figure:: assets/images/logo.svg
   :alt: PyVRP logo
   :figwidth: 100%

PyVRP is an open-source, state-of-the-art vehicle routing problem (VRP) solver.
It currently supports VRPs with:

* Pickups and/or deliveries between depots and clients (capacitated VRP, VRP with simultaneous pickup and delivery, VRP with backhaul);
* Vehicles of different capacities, costs, and shift durations (heterogeneous fleet VRP);
* Time windows, client service durations, and release times (VRP with time windows and release times);
* Multiple depots (multi-depot VRP);
* Optional clients with prizes for visiting (prize collecting, team orienteering problem).

The implementation builds on `HGS-CVRP <https://github.com/vidalt/HGS-CVRP/>`_, but has been completely redesigned to be easy to use as a highly customisable Python package, while maintaining speed and state-of-the-art performance.
This allows users to directly solve VRP instances, or implement variants of the HGS algorithm using Python, inspired by the examples in this documentation. 
Users can customise various aspects of the algorithm using Python, including population management, crossover strategies, granular neighbourhoods and operator selection in the local search.

The PyVRP package comes with pre-compiled binaries for Windows, Mac OS and Linux, and can thus be easily installed without requiring local compilation.
It can be installed through *pip* via

.. code-block:: shell

   pip install pyvrp

.. hint::

    If you are new to vehicle routing or metaheuristics, you might benefit from first reading the :doc:`introduction to VRP <setup/introduction_to_vrp>`, :doc:`introduction to HGS <setup/introduction_to_hgs>`, and :doc:`tutorial <../examples/quick_tutorial>` pages.
    To set up an installation from source, or to run the examples listed below yourself, please have a look at the :doc:`installation instructions <setup/installation>`.

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   setup/introduction_to_vrp
   setup/introduction_to_hgs
   setup/installation
   setup/getting_help
   setup/benchmarks
   setup/citing

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/quick_tutorial
   examples/basic_vrps
   examples/using_pyvrp_components

.. toctree::
   :maxdepth: 1
   :caption: API reference

   api/pyvrp
   api/crossover
   api/diversity
   api/repair
   api/search
   api/plotting
   api/stop

.. toctree::
   :maxdepth: 1
   :caption: Developing PyVRP

   dev/benchmarking
   dev/contributing
   dev/supported_vrplib_fields
   dev/new_vrp_variants
