# Nextmv Java Gurobi Knapsack

Example for running a Java `Maven` application on the Nextmv Platform using the
Gurobi solver. We solve a knapsack Mixed Integer Programming problem.

1. Setup license:
    1. **Local**: Add license file `gurobi.lic` to the root of the project.
        - If not using VS-Code's dev container, just place the `gurobi.lic` file
          in `$HOME/gurobi.lic` (Gurobi's default path for the license).
    1. **Platform**: Don't forget to also define the license file as a
        [secret][secret] in your Nextmv Application as well. This can be easily
        done via [console].
1. Generate a `main.jar`.

    ```bash
    mvn package
    ```

1. Run the app.

    ```bash
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
[blog]: https://www.nextmv.io/blog
[contact]: https://www.nextmv.io/contact
