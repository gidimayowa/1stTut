using UnityEngine;

public class PipeCollision : MonoBehaviour
{
    private void OnTriggerEnter2D(Collider2D collision)
    {
        // Only react when the Bird hits this collider
        if (collision.CompareTag("Bird"))
        {
            Debug.Log("Bird hit a pipe!");
        }
    }
}