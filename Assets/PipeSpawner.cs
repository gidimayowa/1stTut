using UnityEngine;

public class PipeSpawner : MonoBehaviour
{
    // Prefab of the Pipe (parent object containing top + bottom pipes)
    // This is what we will spawn each time.
    [Header("Pipe Settings")]
    public GameObject pipePrefab;

    // How many seconds between each pipe spawn.
    public float spawnInterval = 2f;

    // How much random vertical variation the pipe can have.
    // Example: heightOffset = 2 means pipes can spawn between -2 and +2 on Y-axis.
    public float heightOffset = 2f;

    // Internal timer that counts down every frame
    private float timer;

    void Start()
    {
        // Spawn the first pipe IMMEDIATELY when the game begins
        SpawnPipe();

        // Set the timer so the next pipe spawns after the normal interval
        timer = spawnInterval;
    }

    void Update()
    {
        // Reduce the timer based on time passed since last frame
        timer -= Time.deltaTime;

        // When timer reaches zero or below, it's time to spawn a pipe
        if (timer <= 0f)
        {
            SpawnPipe();

            // Reset timer so the next pipe waits the full spawnInterval seconds
            timer = spawnInterval;
        }
    }

    void SpawnPipe()
    {
        // Pick a random Y value between -heightOffset and +heightOffset
        float randomY = Random.Range(-heightOffset, heightOffset);

        // Make the spawn position:
        // - X comes from the spawner's position (usually far right)
        // - Y is the spawner's Y + random offset
        // - Z stays at 0
        Vector3 spawnPos = new Vector3(transform.position.x, transform.position.y + randomY, 0);

        // This creates a NEW pipe object in the scene at the given position
        // The pipePrefab already contains the top + bottom pipes as children.
        Instantiate(pipePrefab, spawnPos, Quaternion.identity);

        // NOTE:
        // This script does NOT remove or destroy old pipes.
        // That responsibility is in the PipeMoveScript, which destroys
        // pipes when they move off the left side of the screen.
    }
}
