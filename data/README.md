# Pre-processing

## <span style="color:lightblue">Label-Studio</span>

### <span style="color:lightgreen">Docker</span>

[Volume](https://drive.google.com/drive/folders/1lfZTfyBITK0RF8ZWTQt7y9NxC_q-sGEZ)

```sh
docker run -it -p 8080:8080 -v ${PWD}/label-studio/data:/label-studio/data heartexlabs/label-studio:latest label-studio --log-level DEBUG
```
