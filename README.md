# Upload-Bypass

`upload-bypass.py` generates a wordlist of candidate filenames for testing file-upload filters

It applies a wide range of filename bypass techniques. Double extension, reverse double extension, case shuffle, URL-encoded dots, null-byte cutoffs, name overflow, path traversal, trailing characters, IIS wildcard characters, slash-in-extension, RTL override and NTFS ADS. And prints the resulting names, one per line, ready to load into your fuzzer

It only generates names, never uploads anything and makes no network requests. The workflow is:

1. generate the wordlist
2. fuzz the upload endpoint to find which filenames get through
3. serve one of the ready-made payloads from `payloads/` at an accepted filename

It can also export flat, one-per-line lists ready to load into Burp Intruder: the bypass tokens like %00 / %2e / ::$data (`--save-bypasses`), the executable extensions (`--save-extensions`) and the allowed formats (`--save-allowed-extensions`)

## Why

Checking which of the hundreds of filename permutations a filter lets through is tedious by hand (a single `-E php -A jpg` run yields ~750 names), so `Upload-Bypass` produces them all in one pass, letting you brute-force them and only hand-test the ones that upload

## Usage

```bash
python3 upload-bypass.py -E php -A jpeg                              # php names, allowed format jpeg
python3 upload-bypass.py -E php -A png -o names.txt                  # save the wordlist to a file
python3 upload-bypass.py -E jar -A jpeg                              # a single/custom extension
python3 upload-bypass.py -E php -A jpeg,png                          # several allowed formats
python3 upload-bypass.py --all-extensions --all-allowed-extensions   # everything
python3 upload-bypass.py --list-extensions                           # show the executable extensions
python3 upload-bypass.py --list-allowed-extensions                   # show the allowed formats
python3 upload-bypass.py --save-bypasses tokens.txt                 # bypass tokens (%00, %2e, ::$data, ...), one per line
python3 upload-bypass.py --save-extensions exts.txt                  # executable extensions, one per line
python3 upload-bypass.py --save-allowed-extensions allow.txt         # allowed extensions, one per line
python3 upload-bypass.py -E php -A gif --overflow-length 236         # upload-by-URL / wget truncation trick
```

## Help

```text
usage: upload-bypass.py [-h] [-E EXTENSION] [--all-extensions] [--list-extensions] [--save-extensions FILE] [--overflow-length N] [-A EXTENSION]
                        [--all-allowed-extensions] [--list-allowed-extensions] [--save-allowed-extensions FILE] [--save-bypasses FILE] [-n FILENAME] [-o OUTPUT]

general:
  -h, --help                      Show this help message

executable extension:
  -E, --extension EXTENSION       Extension of the file you want to execute, a family or comma-separated (e.g. php or jar,war)
  --all-extensions                Use every available executable extension to build the wordlist
  --list-extensions               List the available extensions
  --save-extensions FILE          Save the executable extensions as a flat list (one per line)
  --overflow-length N             Truncation length for the name-overflow trick (e.g. 255 filesystem, 236 wget), default 255

allowed extension:
  -A, --allowed EXTENSION         Extension the app accepts, one or comma-separated (e.g. jpeg or jpeg,png)
  --all-allowed-extensions        Use every available allowed extension to build the wordlist
  --list-allowed-extensions       List the allowed extensions
  --save-allowed-extensions FILE  Save the allowed extensions as a flat list (one per line)

bypasses:
  --save-bypasses FILE            Save the bypass tokens (%00, %2e, ::$data, ...) as a flat list, one per line

output:
  -n, --filename FILENAME         Base filename (e.g. -n avatar), default shell
  -o, --output OUTPUT             Save the list to a file (e.g. -o names.txt), otherwise printed to stdout
```

## Executable extensions (`-E`)

| Family | Extensions |
| --- | --- |
| `php` | php, php3, phar, phtml, php5, php6, php7, php8, phps, pht, phtm, phpt, php4, pgif, php2, inc, hphp, ctp, module |
| `asp` | asp, aspx, config, ashx, asmx, aspq, axd, cshtm, cshtml, rem, soap, vbhtm, vbhtml, asa, cer, shtml, xamlx, shtm, stm |
| `jsp` | jsp, jspx, jsw, jsv, jspf, wss, do, action, actions |
| `java` | jar, war, ear |
| `coldfusion` | cfm, cfml, cfc, dbm, cFm, cFml, cFc, dBm |
| `perl` | pl, cgi, pm, lib |
| `python` | py, pyc, pyw, pyz, wsgi, cgi |
| `ruby` | rb, rhtml, erb, ru, cgi |
| `node` | js, json, node |
| `flash` | swf |
| `erlang` | yaws |

You can also pass any extension directly (`-E jar`, `-E jar,war,jsp`)

## Allowed formats (`-A`)

| | |
| --- | --- |
| Known allow-list | jpg, jpeg, png, gif, pdf, mp3, mp4, txt, csv, svg, xml, xlsx, webp, bmp, tiff, docx, zip, json |

Any other value is accepted too (`-A heic`)

## Payloads

Ready-to-use files to serve once you know which extension gets through, drop them straight into your exploit server or upload point:

| File | What it is |
| --- | --- |
| `webshell.php` / `.asp` / `.aspx` / `.jsp` / `.cfm` / `.pl` / `.py` / `.rb` / `.js` / `.yaws` | Command webshell per language (`?cmd=id`); `.cfm` is real ColdFusion via `<cfexecute>`, `.js` is Node.js, `.yaws` is Erlang/Yaws |
| `webshell.war` | Java webshell. A WAR (zip containing a JSP) that Tomcat/JBoss auto-deploys to `/webshell/index.jsp?cmd=id` |
| `webshell-script.php` | PHP webshell using `<script language="php">` (bypasses `<?php` filtering) |
| `polyglot.jpg` / `.png` / `.gif` | Valid image (JPEG/PNG/GIF) that also runs as PHP, host it under a bypass name like `shell.php.jpg` |
| `xxe.svg` | SVG with an XXE payload that reads `/etc/passwd` |
| `xss.svg` | SVG with a stored-XSS payload |
| `.htaccess` | Maps the `.arbit` extension to be executed as PHP (upload this first) |
| `shell.arbit` | PHP webshell with the `.arbit` extension (upload after `.htaccess`) |
| `web.config` | IIS: executes `.config` as ASP (drop into an IIS directory) |
| `uwsgi.ini` | uWSGI: runs a command when the `.ini` is parsed (restart/crash/autoreload) |
| `webshell.shtml` | Server-Side Includes webshell (`<!--#exec cmd -->`), runs a fixed command set in the file (SSI can't read URL params) |
| `eicar.txt` | EICAR antivirus test string (check whether an AV is present) |

## Samples

Clean, harmless example files of every format (`sample.jpg`, `sample.png`, `sample.pdf`, ...), for the discovery step: upload a clean sample of each format to find out which one the app accepts, so you don't have to hunt for a real image/pdf/etc online. These are not payloads, they contain no attack code

## Author & License

Upload-Bypass by **justice-reaper**. Released under the [MIT License](LICENSE): free to use, modify and distribute, provided the copyright notice is kept
