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

## References

- [Google OR-Tools](https://github.com/or-tools/or-tools)
- [Google OR-Tools Java Examples](https://github.com/or-tools/java_or-tools)
