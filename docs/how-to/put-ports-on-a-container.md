# Put ports on a container's edge

This guide shows how to draw [ports](../explanation/glossary.md#port), the
small markers on the border of a container where its links start and end, as
component diagrams in UML do. D2 places every shape inside its container, away
from the border, so `markdown-d2` moves each port onto the edge after D2 has
laid the diagram out.

## Mark a shape as a port

A shape becomes a port when it carries the class `port-left` or `port-right`,
which names the edge it moves to. Your own classes decide what the marker
looks like, and the two port classes are the place to say where its name goes:
next to the marker, on the inside of the container.

```d2 title="A container with ports"
direction: right
classes: {
  port-left: {label.near: outside-right-center}
  port-right: {label.near: outside-left-center}
  asks: {shape: circle; width: 16; height: 16; style.fill: transparent}
  shares: {shape: circle; width: 8; height: 8; style: {fill: transparent; stroke-width: 8}}
}
heater: Heater {
  target {class: [asks; port-left]}
  power {class: [asks; port-left]}
  temperature {class: [shares; port-right]}
}
```

````markdown
```d2 title="A container with ports"
direction: right
classes: {
  port-left: {label.near: outside-right-center}
  port-right: {label.near: outside-left-center}
  asks: {shape: circle; width: 16; height: 16; style.fill: transparent}
  shares: {shape: circle; width: 8; height: 8; style: {fill: transparent; stroke-width: 8}}
}
heater: Heater {
  target {class: [asks; port-left]}
  power {class: [asks; port-left]}
  temperature {class: [shares; port-right]}
}
```
````

Separate the classes in the list with `;`. With a comma, D2 reads
`asks, port-left` as one class name it does not know and reports nothing, so
the shape stays where D2 put it.

The `shares` marker is filled through a stroke as wide as the marker, not
with `style.fill`, because D2 refuses a theme colour in `style.fill` and a
fixed colour stays the same in the dark [theme](../explanation/glossary.md#theme).
The stroke follows the theme. An icon does not, since its colours are fixed in
its file.

!!! warning "Ports need direction: right and the dagre layout"

    `direction: right` makes D2 stack the ports of a container in one column.
    Without it, D2 puts them in one row, so they land on one spot once they
    move to the edge, and the build stops with
    `overlaps port ...; use direction: right`. The build also stops when the
    diagram picks the `elk` [layout engine](../explanation/glossary.md#layout-engine),
    because ports work only with `dagre`, D2's default.

## Link two containers port to port

A port links to a port in another container like any two shapes. Write each
link with `--`, the left container first:

```d2 title="Two containers linked port to port"
direction: right
classes: {
  port-left: {label.near: outside-right-center}
  port-right: {label.near: outside-left-center}
  asks: {shape: circle; width: 16; height: 16; style.fill: transparent}
  shares: {shape: circle; width: 8; height: 8; style: {fill: transparent; stroke-width: 8}}
}
heater: Heater {
  temperature {class: [shares; port-right]}
  target {class: [asks; port-right]}
}
display: Display {
  temperature {class: [asks; port-left]}
  target {class: [shares; port-left]}
}
heater.temperature -- display.temperature
heater.target -- display.target
```

````markdown
```d2 title="Two containers linked port to port"
direction: right
classes: {
  port-left: {label.near: outside-right-center}
  port-right: {label.near: outside-left-center}
  asks: {shape: circle; width: 16; height: 16; style.fill: transparent}
  shares: {shape: circle; width: 8; height: 8; style: {fill: transparent; stroke-width: 8}}
}
heater: Heater {
  temperature {class: [shares; port-right]}
  target {class: [asks; port-right]}
}
display: Display {
  temperature {class: [asks; port-left]}
  target {class: [shares; port-left]}
}
heater.temperature -- display.temperature
heater.target -- display.target
```
````

D2 lines each port up with the port it links to, so the links run straight.
D2 lays out a link with no arrowhead in the order you wrote it, so the two
containers stay side by side. With `->` or `<-`, D2 places the containers to follow
the arrows instead, so two containers that link both ways end up one above the
other, with links that cross.

The side of a port is yours to choose and says nothing about which way data
moves: a port on the left edge can start a link as well as end one.

## Highlight a port in a scenario

A scenario or a step that gives a port a class replaces the port's classes
rather than adding to them. List the marker and port classes again next to
the new one, or the shape stops being a port on that
[board](../explanation/glossary.md#board):

```d2 title="One port highlighted"
direction: right
classes: {
  port-left: {label.near: outside-right-center}
  port-right: {label.near: outside-left-center}
  asks: {shape: circle; width: 16; height: 16; style.fill: transparent}
  shares: {shape: circle; width: 8; height: 8; style: {fill: transparent; stroke-width: 8}}
  current: {style.stroke-width: 4}
}
heater: Heater {
  temperature {class: [shares; port-right]}
}
display: Display {
  temperature {class: [asks; port-left]}
}
heater.temperature -- display.temperature
scenarios: {
  reading: {
    display.temperature.class: [current; asks; port-left]
  }
}
```

````markdown
```d2 title="One port highlighted"
direction: right
classes: {
  port-left: {label.near: outside-right-center}
  port-right: {label.near: outside-left-center}
  asks: {shape: circle; width: 16; height: 16; style.fill: transparent}
  shares: {shape: circle; width: 8; height: 8; style: {fill: transparent; stroke-width: 8}}
  current: {style.stroke-width: 4}
}
heater: Heater {
  temperature {class: [shares; port-right]}
}
display: Display {
  temperature {class: [asks; port-left]}
}
heater.temperature -- display.temperature
scenarios: {
  reading: {
    display.temperature.class: [current; asks; port-left]
  }
}
```
````

[Show a diagram one step at a time](show-steps.md) explains scenarios and
steps.
