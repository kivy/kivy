# Video provider demos

Manual / interactive demos for the Kivy 3.0 video stack.

## `avfoundation_demo.py`

Visual test bed for the macOS / iOS AVFoundation provider and for the
`VideoBase` API surface added in 3.0:

- `Video.generate_thumbnail(...)` — driven by the thumbnail card on the
  grid screen.
- `options={...}` — toggles on the player screen map to keys on the
  options dict forwarded to the AVFoundation provider. Construction-time
  hints; take effect on the next *Apply (reload)*.
  - `force_cpu_copy` flips the AVFoundation provider between its
    zero-copy IOSurface → ANGLE pbuffer → `GL_TEXTURE_2D` path and the
    CPU-`memcpy` fallback so you can A/B the two on the same clip.
  - `automatically_waits_to_minimize_stalling` forwards directly to the
    `AVPlayer` property of the same name. With it off, AVPlayer starts
    playback as soon as the first decodable frame is available rather
    than buffering ahead — useful for low-latency UX, more likely to
    surface `buffering=True` transitions on a borderline link.

The catalog mixes two kinds of clips:

- **Progressive H.264/MP4 downloads** — cached once to
  `~/.kivy/video_demo_cache/`. Small (~4 MB) Big Buck Bunny and Sintel
  trailers from the Blender Foundation when you want H.264 + AAC,
  small (~5 MB) Big Buck Bunny 720p for the quickest smoke test, and
  1080p (~30 MB) clips for high-resolution pixel-path comparison.

  Note that the test-videos.co.uk standardised clips (Big Buck Bunny
  720p, Sintel 1080p, Jellyfish 1080p) are deliberately published
  *without* an audio track — they're synthetic, fixed-bitrate test
  files for codec / network benchmarking. The two Blender Foundation
  trailers carry AAC audio.
- **HLS streams** — Apple's public BipBop reference set, in both TS
  and fMP4 ladders. These are passed straight to AVFoundation; there's
  no local cache, AVPlayer downloads the manifest + segments itself.
  Both BipBop streams carry the classic "bip… bop" audio jingle.

Run from the source-tree root:

    python examples/widgets/video/avfoundation_demo.py

Or from this directory:

    python avfoundation_demo.py

### What to verify

1. **Thumbnail grid populates** — once each remote clip finishes
   downloading, its card should show a representative frame.
2. **`force_cpu_copy` A/B** — toggle the checkbox + *Apply (reload)*.
   Frames should look identical in both paths. The CPU path is
   noticeably more CPU-hungry on a 1080p clip.
3. **`automatically_waits_to_minimize_stalling = False`** — start-up
   time after *Apply (reload)* should feel snappier; on a borderline
   link you should also see the buffering overlay flicker on/off more
   readily during the first few seconds of playback.
4. **Audio** — use either Blender Foundation trailer (Big Buck Bunny
   or Sintel) or either BipBop stream to exercise the volume control.
   The three test-videos.co.uk clips (Big Buck Bunny 720p, Sintel
   1080p, Jellyfish 1080p) are video-only by design.
