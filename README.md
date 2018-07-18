[![Build Status](https://api.travis-ci.org/misho104/yaslha.svg?branch=master)](https://travis-ci.org/misho104/yaslha)
[![Coverage Status](https://coveralls.io/repos/github/misho104/yaslha/badge.svg?branch=master)](https://coveralls.io/github/misho104/yaslha?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-ff25d1.svg)](https://github.com/misho104/yaslha/blob/master/LICENSE)

[yaslha](https://github.com/misho104/yaslha): Yet Another SLHA module for Python3
=================================================================================

A Python3 package to manipulate [SLHA](http://skands.physics.monash.edu/slha/) files and convert them to other file formats (JSON and YAML).

Quick Start
-----------

(TBW)

Introduction
------------

The [SUSY Les Houches Accord](http://skands.physics.monash.edu/slha/) is a data format widely used in particle physics phenomenology.
It is originally defined in [arXiv:hep-ph/0311123](https://arxiv.org/abs/hep-ph/0311123) and extended to SLHA2 in [arXiv:0801.0045](https://arxiv.org/abs/0801.0045).

Because of its birth in FORTRAN era it is a fixed length format such as

```
BLOCK SMINPUTS                  # Standard Model input parameters
     1     1.27934000e+02   # alpha_em^-1(M_Z)^MSbar
     2     1.16637000e-05   # G_F [GeV^-2]
     3     1.17200000e-01   # alpha_S(M_Z)^MSbar
     4     9.11876000e+01   # mZ (pole)
     5     4.18000000e+00   # mb(mb)^MSbar
     6     1.73300000e+02   # mt (pole)
     7     1.77682000e+00   # mtau (pole)
#
BLOCK ALPHA                    #
          -2.68630018e-02   # Higgs mixing parameter
#
BLOCK HMIX Q= 2.00000000e+02   # Higgs parameters (DRbar)
     1     5.40000000e+02   # mu(Q)
     2     4.00000000e+01   # tanbeta(Q)
     3     2.46220569e+02   # vev(Q)
     4     2.30400000e+05   # mA^2(Q)
#
...
```

and extended in many program codes.

Python has two famous SLHA parser: [PySLHA](http://www.insectnation.org/projects/pyslha) by Andy Buckley and [pylha](https://github.com/DavidMStraub/pylha) by David M. Straub.
[yaslha](https://github.com/misho104/yaslha) is "yet another" SLHA parser, influenced much by these two parsers.

Python regrettably experienced a terrible era due to the transition from Python2 to Python3.
To reduce code complexity, this package supports only Python3.4 and later versions.

Usage
-----

(TBW)

Author
------

[Sho Iwamoto / Misho](https://www.misho-web.com/), under much influence from [PySLHA](http://www.insectnation.org/projects/pyslha) by Andy Buckley and [pylha](https://github.com/DavidMStraub/pylha) by David M. Straub.