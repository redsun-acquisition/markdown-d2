# My site

<!-- --8<-- [start:first] -->
```d2
you -> page: write
page -> site: build
```
<!-- --8<-- [end:first] -->

<!-- --8<-- [start:steps] -->
```d2 title="Making a cup of tea"
kettle: boil the water
steps: {
  1: { cup: pour it in a cup; kettle -> cup }
  2: { tea: add the tea; cup -> tea }
}
```
<!-- --8<-- [end:steps] -->
