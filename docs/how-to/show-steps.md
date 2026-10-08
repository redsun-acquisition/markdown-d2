# Show a diagram one step at a time

This guide shows how to split a diagram into [steps](../explanation/glossary.md#step)
your reader moves through, and how to choose the animation between them.

## Split the diagram

Write the steps in the diagram with D2's `steps` keyword. Each step starts
from the one before and adds to it:

```d2 title="Publishing a site"
pages: write the pages
steps: {
  1: { build: build the site; pages -> build }
  2: { check: check the links; build -> check }
  3: { publish: publish it; check -> publish }
}
```

````markdown
```d2 title="Publishing a site"
pages: write the pages
steps: {
  1: { build: build the site; pages -> build }
  2: { check: check the links; build -> check }
  3: { publish: publish it; check -> publish }
}
```
````

The figure shows the diagram without its steps first, then each step in turn,
with buttons and a counter to move between them.

If each picture should start from a blank page, use `layers` instead of
`steps`; if each should start from the diagram without its steps, use
`scenarios`. The figure treats every layer and scenario as a step too. The
D2 documentation on [composition](https://d2lang.com/tour/composition) shows
all three.

## Explain each step

Give a board a `label`, and its text shows above the picture and changes as
the reader steps. The top board takes its label at the start of the diagram,
and each step, layer or scenario takes one inside its own map:

```d2 title="Making tea" transition="fade"
label: "Everything starts with the kettle."
kettle
steps: {
  1: { label: "Pour the water once it boils."; cup; kettle -> cup }
  2: { label: "Add the tea last."; tea; cup -> tea }
}
```

````markdown
```d2 title="Making tea" transition="fade"
label: "Everything starts with the kettle."
kettle
steps: {
  1: { label: "Pour the water once it boils."; cup; kettle -> cup }
  2: { label: "Add the tea last."; tea; cup -> tea }
}
```
````

A board without a label shows no text.

## Choose the transition

Each new step fades in, unless you pick another
[transition](../explanation/glossary.md#transition) for the block with its
`transition` option:

- `morph` slides each shape that two steps share to its new place and fades in
  the new ones, so the reader can follow what moved.
- `none` switches at once.
- `fade`, the default, fades the new step in.

```d2 title="A morph" transition="morph"
direction: right
browser
steps: {
  1: { server; browser -> server }
  2: { cache; cache -> browser }
}
```

````markdown
```d2 title="A morph" transition="morph"
direction: right
browser
steps: {
  1: { server; browser -> server }
  2: { cache; cache -> browser }
}
```
````

To change the transition of every diagram on the site, set `transition` in the
[formatter's](../explanation/glossary.md#formatter) `kwds` in `zensical.toml`; a block's own option still wins:

```toml
format = { object = "markdown_d2.formatter", kwds = { root = "docs", transition = "morph" } }
```

A reader whose system asks for less motion sees every change at once, whatever
you choose.

## Present a diagram

The full-screen button opens the diagram over the page, with the same step
buttons and the arrow keys, so you can walk an audience through it. The
[controls](../reference/figure.md#controls) lists every button and key.
