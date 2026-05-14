# Asset Manifest Service Stub

The asset manifest service serves immutable image/audio manifest versions. Apps download or package assets separately, then resolve the best local asset in this priority order:

1. final
2. reviewed
3. generated or synthetic draft
4. placeholder

The child app never calls image, TTS, sound effect, upscaling, or layer extraction providers.
