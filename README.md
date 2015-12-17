# Description

fingerprinter is a tool that takes as input a list of URLs, and which outputs, for each URL, a score indicating if remote website is using Ruby on Rails. This tool was written in Python 3.

Example:
```
python fingerprinter.py    https://www.phusionpassenger.com/ https://squareup.com/
Score    URL  
4 / 5    https://www.phusionpassenger.com/
3 / 5    https://squareup.com/
```
## How to install

```
$ git clone https://github.com/bdesbiolles/fingerprinter.git
```
install beautifulsoup4 and requests modules either via pip or distribution packages.

```
$ pip install requests
$ pip install beautifulsoup4
$ cd fingerprinter
```
## Usage

```
usage: fingerprinter.py [-h] [-v] URL [URL ...]

indicate if remote website is using RoR

positional arguments:
  URL            website url

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  increase output verbosity

```

## Details

The heuristics are loaded via the data/heuristics.json file.

Example:
```
{
  "headers" : {
    "samplefield": "regex"
  },
  "meta" : {
    "name": "content matching regex"
  },
  "script" : "src matching regex",
  "link" : "href matching regex"
  }
}
```
You can add headers and meta fields and change the regular expressions.

The default parameters are:
```
Headers :
  Server: check for mod_rails, mod_rack or Phusion Passenger
  X-Powered-By: check for mod_rails, mod_rack or Phusion Passenger
meta:
  csrf-param: authenticity_token
script: /assets/
link: /assets/
```
* The assets rule is based on : http://guides.rubyonrails.org/asset_pipeline.html
* The Header and meta: https://stackoverflow.com/questions/14264780/detect-if-rails-is-running-a-site
