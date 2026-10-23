# Contributing

If you'd like to contribute to the token sheets, we'd greatly appreciate it! Listed below are the main ways you can help us out and what each entails.

## Verifying Translations

Does a translation have a typo? Is there a variant name that should be added? We appreciate any and all small fixes to the sheets, which you can help us spot simply by using them.

## Adding New Translations

One important goal of this project is to maintain token translations for every language supported by TI, and there are a lot! Each language's token and font translations are bundled in a localization app (`.8xk`, `.8ck`, or `.8ek`). The [localization extraction tools](https://github.com/TI-Toolkit/token_translation_extractor) recover native strings, replacement glyphs, and version evidence from these files and reproduce the XML additions. We _strongly_ recommend using these tools instead of manually transcribing information from a calculator.

Application revisions are independent of OS versions. Review the documented timeline policy before adding a new XML boundary, and verify effective locale names with English fallback to catch collisions across active ranges.

Built-in translations in TI-83-family ROMs are extracted separately with the extractor repository's `locales.rom` module. Keep the ROM's actual model and OS revision, including French `frN` suffixes, and retain its native bytes and font evidence. Model order tracks token-table lineage, rather than calendar release order.

## Adding New Scripts

If you've written a script involving the token sheets that has general utility, feel free to make a PR to add it to the `scripts` package. Be sure to document your code and add relevant imports to `__init__.py` so it may be incorporated into the package.
