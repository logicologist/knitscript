This repository is for KnitScript, a DSL for creating knitting patterns.

* [Project pre-proposal][preproposal]
* [Project proposal][proposal]
* [Design document][designdoc]
* [Final report][report]
* [Poster slides][poster]
* [Demo video][demo]

## Getting started ##

This project requires Python version 3.7 or higher.

This project also requires the [ANTLR](https://www.antlr.org/download.html)
tool (version 4) and the Python ANTLR runtime. Basically, you need two things:

1. Either `antlr4` or `antlr` should be in your PATH. This happens
   automatically if you install ANTLR using Homebrew on Mac or Chocolatey on
   Windows.
2. The `antlr4-python3-runtime` Python package should be installed using pip.

When running KnitScript for the first time, run `python setup.py build`. To
compile a .ks file called `myfilename.ks`, run `python -m knitscript
myfilename.ks`.

Running `python setup.py develop` allows a .ks file to be run simply with the
command `knitscript myfilename.ks`.

To learn how to use KnitScript, please see our [language tutorial][tutorial].

## License ##

KnitScript is open-sourced under the MIT license.


[preproposal]: https://docs.google.com/document/d/1xOmiT00jGZlY3KzcF18slLTcPjzgHZ_5Ry3rLuTQCTk/edit?usp=sharing
[proposal]: https://docs.google.com/document/d/1HJaMU6nQh7hZbXyaBIFYdoHr-XjVUfyUXAm2qFd-q9o/edit?usp=sharing
[designdoc]: https://docs.google.com/document/d/1bXGWBJ_lnPc5Xc-QCefcFH5KNZkcsYDslpOo9RWE-is/edit?usp=sharing
[report]: https://docs.google.com/document/d/1aYORpi4gq3Y1R5aTd2yqlDE1VDverKlRFNv3xR3BcdQ/edit?usp=sharing
[poster]: https://drive.google.com/file/d/1F9-DcAWweqWQZeE_HwzfticYpjIXfc7i/view?usp=sharing
[demo]: https://drive.google.com/file/d/1QSRcMQy7tzoCxKIZ2CbPNWYG9alXEeUx/view?usp=sharing
[tutorial]: https://docs.google.com/document/d/1TqBz_DOn-wV0VecZOt3qUNojs47AlXf_VJXSXezxab4/edit?usp=sharing