using UnityEngine;

public class PipeMoveScript : MonoBehaviour
{
    [Header("Movement Settings")]
    public float speed = 2f;        // How fast the pipe moves to the left
    // The X position threshold. If the pipe passes this X value, it will be destroyed.
    public float destroyX = -50f;   

    private BoxCollider2D myBoxCollider;

    void Start()
    {
        myBoxCollider = GetComponent<BoxCollider2D>();
    }

    // Update is called once per frame
    void Update()
    {
        // Move the whole Pipe object (and its children) to the left
        transform.position += Vector3.left * speed * Time.deltaTime;

        // When the pipe is far off the left side of the screen, destroy it
        if (transform.position.x < destroyX)
        {
            Destroy(gameObject);
        }
    }
}
