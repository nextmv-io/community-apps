# Java OR-Tools Maven Example

Sample project explaining how to use Google OR-Tools in a maven project that can
be executed on the Nextmv platform.

## Usage

Java templates in Nextmv require a `main.jar` as an entry point. Running the
following command will generate a `main.jar` in the root direcotry of the
project.

```bash
mvn package
```

After that you can run the `main.jar` file with the following command:

```bash
java -jar main.jar --input input.json
```

You can also push the `main.jar` file to the Nextmv Cloud and run it remotely.
Take a look at the documentation on how to
[deploy](https://www.nextmv.io/docs/platform/deploy-app/custom-apps) and
[run](https://www.nextmv.io/docs/platform/run-app-remotely/nextmv-cli) an app in
the Nextmv Cloud.

## Mirror running on Nextmv Cloud locally

Pre-requisites: Docker needs to be installed.

To run the application locally in the same docker image as the one used on the
Nextmv Cloud, you can use the following command:

```bash
mvn package && cat input.json | docker run -i --rm \
-v $(pwd):/app ghcr.io/nextmv-io/runtime/java:latest \
java -jar /app/main.jar
```

You can also debug the application by running it in a Dev Container. This
workspace recommends to install the Dev Container extension for VSCode. If you
have the extension installed, you can open the workspace in a container by using
the command `Dev Containers: Reopen in Container`.

## References

- [Google OR-Tools](https://github.com/or-tools/or-tools)
- [Google OR-Tools Java Examples](https://github.com/or-tools/java_or-tools)
