# Nextmv Java Gurobi Multi-Knapsack

Example for running a Java `Maven` application on the Nextmv Platform using the
Gurobi solver. We solve a multi-knapsack Mixed Integer Programming problem while
reading the input from an _Excel_ file and writing the output to an _Excel_
file.

1. Setup license:
    1. **Local**:
        - You can simply place the `gurobi.lic` file in your _home directory_
        (like Gurobi expects it). If you are using the dev container, it will be
        mounted inside of the container for you.
    1. **Platform**: Don't forget to also define the license file as a
        [secret][secret] in your Nextmv Application as well. This can be easily
        done via [console].
        - Define a file secret with the name `gurobi.lic` and the content of
          your license file.
        - Define an environment variable secret with the name `GRB_LICENSE_FILE`
          and the value `./gurobi.lic` to point Gurobi to the license file.
1. Generate a `main.jar`.

    ```bash
    mvn package
    ```

1. Run the app (update the input in `inputs/input.xlsx` or point to a different
   directory via `-input` option).

    ```bash
    java -jar main.jar
    ```

1. If above steps were successful, you can push the app to the Nextmv Platform.
   E.g., using the [Nextmv CLI][install-cli]:

    ```bash
    nextmv push -a <your-app-id>
    ```

1. You can now run the app on the Nextmv Platform by using the [Nextmv
   Console][console] or via the [Nextmv CLI][install-cli]:

    ```bash
    nextmv run -a <your-app-id> -s <your-secret-id> -i inputs/ --content-type multi-file
    ```

## Mirror running on Nextmv Cloud locally

Docker needs to be installed.

To run the application in the same Docker image as the one used on Nextmv
Cloud, you can use the following command:

```bash
mvn package | docker run -i --rm \
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
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
