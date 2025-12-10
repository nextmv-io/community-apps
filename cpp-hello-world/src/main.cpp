#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>
#include <cstdlib>
#include <string>
#include <sstream>

std::atomic<bool> keepRunning(true);

/**
 * Function to stress memory by allocating a specified amount of memory.
 * The memory stays allocated while keepRunning is true.
 */
void stressMemory(int memoryMB)
{
    std::cerr << "Starting memory stress test with " << memoryMB << " MB." << std::endl;
    const size_t blockSize = 1024 * 1024; // 1MB
    std::vector<char> memory(memoryMB * blockSize);
    // Keep the memory allocated while the program is running
    while (keepRunning)
    {
        // Optionally, you can touch the memory to prevent it from being swapped out
        for (size_t i = 0; i < memory.size(); ++i)
        {
            memory[i] = 0; // Touch the memory
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100)); // Sleep to avoid busy-waiting
    }
    // Memory will be automatically freed when the vector goes out of scope
    std::cerr << "Memory stress test completed." << std::endl;
}

/**
 * Function to stress CPU by performing simple calculations and running for a specified duration.
 * The CPU will be kept busy while keepRunning is true.
 */
void stressCPU(int durationSeconds, int threadIndex)
{
    std::cerr << "Starting CPU stress test in thread " << threadIndex << " for " << durationSeconds << " seconds." << std::endl;
    auto start = std::chrono::steady_clock::now();
    while (keepRunning)
    {
        // Perform some CPU-intensive work
        volatile long long sum = 0; // Use volatile to prevent optimization
        for (long long i = 0; i < 1000000; ++i)
        {
            sum += i; // Simple operation to keep the CPU busy
        }

        // Check if the specified duration has passed, if so, stop the loop
        auto now = std::chrono::steady_clock::now();
        if (std::chrono::duration_cast<std::chrono::seconds>(now - start).count() >= durationSeconds)
        {
            keepRunning = false;
            break;
        }
    }
    std::cerr << "CPU stress test completed in thread " << threadIndex << "." << std::endl;
}

/**
 * Reads all input from stdin and returns it as a string.
 */
std::string readInput()
{
    // Use a stringstream to read all input
    std::stringstream buffer;
    buffer << std::cin.rdbuf();
    return buffer.str();
}

/**
 * Writes the given string to stdout.
 */
void writeOutput(const std::string &output)
{
    std::cout << output;
    std::cout.flush(); // Ensure the output is flushed immediately
}

int main(int argc, char *argv[])
{
    int duration = 5;    // default duration in seconds for -duration=<value>
    int memoryMB = 100;  // default memory usage in MB for -memory=<value>
    int threadCount = 1; // default thread count for -threads=<value>

    // Parse command line arguments.
    for (int i = 1; i < argc; ++i)
    {
        std::string arg = argv[i];
        if (arg.find("-duration=") == 0)
        {
            duration = std::stoi(arg.substr(10));
        }
        else if (arg.find("-memory=") == 0)
        {
            memoryMB = std::stoi(arg.substr(8));
        }
        else if (arg.find("-threads=") == 0)
        {
            threadCount = std::stoi(arg.substr(9));
        }
    }

    // Print the configuration.
    std::cerr << "Configuration - "
              << "Duration: " << duration << " seconds, "
              << "Memory: " << memoryMB << " MB, "
              << "Threads: " << threadCount << std::endl;

    // Read input from stdin.
    std::string input = readInput();

    // Simulate some compute/memory load.
    std::vector<std::thread> threads;

    threads.emplace_back(stressMemory, memoryMB);
    for (int i = 0; i < threadCount; ++i)
    {
        threads.emplace_back(stressCPU, duration, i);
    }

    for (auto &thread : threads)
    {
        if (thread.joinable())
        {
            thread.join();
        }
    }

    // Write output to stdout.
    writeOutput(input);

    return 0;
}
