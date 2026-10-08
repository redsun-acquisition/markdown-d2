# The figure

Each `d2` block becomes one [figure](../explanation/glossary.md#figure). This
page lists what it holds, the classes your CSS can select, and the controls
it gives the reader.

## Markup

The build writes the figure below, with one board per
[board](../explanation/glossary.md#board) of the diagram, the top board
first:

```html
<figure class="markdown-d2" data-transition="fade" aria-label="Publishing a site">
  <div class="markdown-d2-board" data-step="1" data-name="">
    <div class="markdown-d2-light"><svg>...</svg></div>
    <div class="markdown-d2-dark"><svg>...</svg></div>
  </div>
  <div class="markdown-d2-board" data-step="2" data-name="steps.1">...</div>
  <figcaption>Publishing a site</figcaption>
</figure>
```

`aria-label` and `figcaption` are present only when the block has a `title`.
The page also gets one `<style data-markdown-d2>` and one
`<script data-markdown-d2>`; outside `zensical`, every figure carries its own
pair.

## Classes

| class | element |
| --- | --- |
| `markdown-d2` | the figure |
| `markdown-d2-ready` | the figure, once the script has set it up |
| `markdown-d2-board` | one board |
| `markdown-d2-current` | the board the reader sees |
| `markdown-d2-light`, `markdown-d2-dark` | the light and the dark picture of a board |
| `markdown-d2-controls` | the row of buttons above the picture, in the figure and in full screen |
| `markdown-d2-counter` | the step counter, such as `2 / 4 (steps.1)` |
| `markdown-d2-dialog` | the full-screen view |
| `markdown-d2-stage`, `markdown-d2-view` | the area of the full-screen view the reader zooms and pans, and the diagram inside it |
| `markdown-d2-error` | the box that replaces a broken diagram with `errors = "show"` |
| `markdown-d2-focus` | a picture's SVG while the pointer is on one of its shapes |
| `markdown-d2-hovered` | the shape or connection under the pointer |
| `markdown-d2-tooltip` | the box that shows a shape's tooltip |

## Data attributes

| attribute | on | value |
| --- | --- | --- |
| `data-transition` | figure | `none`, `fade` or `morph` |
| `data-step` | board | position of the board, from `1` |
| `data-name` | board | D2 path of the board, `""` for the top board; a name with a dot or a space is quoted, as in `layers."v1.2"` |

## Controls

Above the picture:

| control | action |
| --- | --- |
| Previous step, Next step buttons | show the board before or after, going round at the ends; present when the diagram has more than one board |
| ++arrow-left++, ++arrow-right++ | the same, while the figure has focus |
| Open full screen button | open the full-screen view at the current board |
| pointer on a shape or connection | fade every other shape and connection, and show the shape's tooltip next to the pointer |

In the full-screen view:

| control | action |
| --- | --- |
| Previous step, Next step buttons, ++arrow-left++, ++arrow-right++ | change the board; the figure follows |
| mouse wheel | zoom in or out around the pointer |
| drag | move the diagram |
| Zoom in, Zoom out buttons | zoom by a factor of 1.25 around the top-left corner |
| Reset zoom button (`1:1`) | return to the original size and place |
| pointer on a shape or connection | the same as in the figure |
| Close button, ++esc++ | close the view |

Every button can be reached with ++tab++ and pressed with ++enter++ or
++space++. A reader whose system asks for less motion sees every change of board at once.
Without JavaScript, every board shows, one below the other, the light and
dark pictures still follow the site's mode, and the browser shows a shape's
tooltip itself.
