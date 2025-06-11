# Nextmv Java Hexaly Knapsack

Example for running a Java `Maven` application on the Nextmv Platform using the
Hexaly solver. We solve a knapsack Mixed Integer Programming problem.

1. Setup license:
    1. **Local**: Add license file `license.dat` to the root of the project.
        - If not using VS-Code's dev container, the license file can also be
          placed in other locations that Hexaly recognizes.
    1. **Platform**: Don't forget to also define the license file as a
        [secret][secret] in your Nextmv Application as well. This can be easily
        done via [console].
        - Define a file secret with the name `license.dat` and the content of
          your license file.
        - Define a env variable secret with the name `LD_LIBRARY_PATH` and
          the value `./lib` to point Hexaly to the bundled `*.so` libraries.
1. Since there is no Hexaly Maven package, we need to setup a local one. For
    this, copy the following files into the project:
    - `hexaly.jar` -> `./lib/`
    - `libhexaly135.so` -> `./lib/` (linux/aarch64 flavor for Nextmv Platform)
    - `libhexaly135.so` -> `./local/` (linux/XXX flavor for local development;
      use aarch64 or x86_64 depending on your local machine)
      - If **not** using VS-Code dev containers, the normal hexaly installation
        can be used for local development instead.
    - Above files are available in the [Hexaly releases][hexaly-releases]. If
      you are on x86_64, you need to download both linux architecture versions
      to get the `libhexaly135.so` file for local and platform environment.
1. (Option 1) Open the project (`java-hexaly-knapsack.code-workspace`) in
    VS-Code dev container.
    - If you are using VS-Code and have the Dev Container extension installed,
      you can open the workspace in a container by using the command
      `Dev Containers: Reopen in Container` (via Command Palette).
    - Simply run / debug the app from the debug view or by hitting `F5`.
1. (Option 2) Make `hexaly.jar` available via your local Maven repository.

    ```bash
    mvn install:install-file \
        -Dfile=lib/hexaly.jar \
        -DgroupId=com.hexaly \
        -DartifactId=hexaly \
        -Dversion=1.0.0 \
        -Dpackaging=jar \
        -DgeneratePom=true
    ```

    - This step is not necessary if you are using VS-Code dev containers,
      as the setup provided here will do it for you.
1. Build and run the app.

    ```bash
    mvn package # to generate main.jar
    java -jar main.jar --input input.json
    ```

1. If above steps were successful, you can push the app to the Nextmv Platform.
   E.g., using the [Nextmv CLI][install-cli]:

    ```bash
    nextmv push --app-id <your-app-id>
    ```

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

```bash
mvn package && cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/java:latest \
java -jar /app/main.jar
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

## Next steps

- Open `src/main/java/com/nextmv/example/Main.java` and modify the model.
- Visit our [docs][docs] and [blog][blog]. Need more assistance?
  [Contact][contact] us!

[docs]: https://docs.nextmv.io
[console]: https://cloud.nextmv.io
[secret]: https://www.nextmv.io/docs/using-nextmv/reference/secret-collections
[install-cli]: https://docs.nextmv.io/docs/using-nextmv/setup/install#nextmv-cli
[hexaly-releases]: https://www.hexaly.com/download
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
