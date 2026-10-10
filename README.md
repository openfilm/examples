# OpenFilm examples

Films made with [OpenFilm](https://github.com/openfilm/openfilm), each a folder you can open, play, change and
render.

```sh
git clone https://github.com/openfilm/examples && cd examples
npx -y openfilm@latest open <example>
```

Studio opens the film; `npx openfilm render` makes the MP4.

## What an example holds

A folder with its `film.html`, the pages it cuts together, and the media it uses: everything needed to play and
render it, nothing else.

- No build outputs: rendered frames, caches and exports stay out (Studio rebuilds what it needs).
- No project state: Studio's `.film/` folder (version history, logs, agent sessions) is never published.
- Media is compressed to what the film needs. An example stays small enough to clone quickly; a film that needs
  larger sources names them in its README and how to get them.
- Each example has a `README.md` (what it shows, how it was made, how to change it) and, when it uses media made by
  others, a `CREDITS.md` with each file's source and license.

## Questions and your own films

Ask about an example, or share a film you made from one, in
[OpenFilm's Discussions](https://github.com/openfilm/openfilm/discussions) (Q&A, Show and tell).

## License

The code in this repository (film.html, pages, scripts) is MIT. Media keeps its own license, listed in each
example's `CREDITS.md`; media without an entry there is by the OpenFilm contributors, also under MIT.
