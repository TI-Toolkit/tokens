# TI Toolkit Token Sheets

Here you can find token sheets for the TI-73 and TI-83/84-series calculators to include in external projects. The sheets contain detailed information about every token in a simple XML format. Basic scripts for parsing the sheets are also included.

## How to Use

To include the token sheets in your next project, add them to your repository as a Git submodule via the `git submodule` command. You can target the `built` branch to clone just the sheets without any of the [scripts](#Scripts) or config files. Check out [this project](https://github.com/TI-Toolkit/tivars_lib_py) for an example.

You can also manually include a download of the sheets and/or scripts as needed.

## XML Format

The XML format for `8X.xml` is outlined below; `73.xml` follows a similar schema.

#### Tokens

Each token is stored in a `<token>` tag (perhaps within a `<two-byte>` parent, if the token is two bytes) containing one or more `<version>` tags, which detail the history of the token across OS versions.

```xml
<tokens>
	...
	<token value="$BA">
		<version>...</version>
		<version>...</version>
	</token>
	<two-byte value="$BB">
		<token value="$00">
			<version>...</version>
		</token>
	</two-byte>
	...
</tokens>
```

#### Versions

Each version includes a `<since>` tag, the first OS with that version of the token, and an optional `<until>` tag, the final OS with that version. The remaining tags are translations of that token into available languages.

```xml
<version>
	<since>
		<model>TI-82</model>
		<os-version>1.0</os-version>
	</since>
	<until>
		<model>TI-83</model>
		<os-version>0.0103</os-version>
	</until>
	<lang code="en">...</lang>
</version>
```

#### Translations

Each language translation contains a number of different ways that token is represented on- and off-calc in that language:

* `ti-ascii`: The font bytes corresponding to the token's characters on-calc
* `display`: A Unicode approximation of the token's on-calc appearance
* `<accessible>`: An ASCII or Latin-1 representation of the token that is meant to be easy to type
* `<variant>`: Any other name commonly used to represent the token (may not exist)
	
```xml
<lang code="en" ti-ascii="7528012D3229" display="u(𝑛-2)">
	<accessible>u(n-2)</accessible>
	<variant>u(𝒏-2)</variant>
</lang>
```

> [!WARNING]
> Currently, only English translations are supported. See [our contribution guidelines](CONTRIBUTING.md) for details on adding new translations.

## Other Formats

Alternative token sheet formats, such as JSON, can be found in the `built` branch. These formats are automatically generated whenever an XML sheet is updated, and thus only the XML sheets should be targeted by PR's.

If there's a format you want supported, feel free to open an issue.

## Scripts

The `scripts` package contains Python scripts for parsing and manipulating the token sheets.

* `build.py`: Helper script to generate the `built` branch
* `formats.py`: Convert an XML sheet to another other format, e.g. JSON ([see above](#Other-Formats))
* `parse.py`: Load a sheet or individual tokens into Python objects
* `tokenide.py`: Create or update token files used by [TokenIDE](https://github.com/merthsoft/TokenIDE)
* `trie.py`: Create a trie from a sheet for use in tokenization

Contributions welcome!
