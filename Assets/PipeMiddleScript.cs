using UnityEngine;

public class PipeMiddleScript : MonoBehaviour
{
    public LogicManager logic;   // Reference to your LogicManager script

    void Start()
    {
        // Find the object tagged "Logic" and grab its LogicManager component
        logic = GameObject.FindGameObjectWithTag("Logic").GetComponent<LogicManager>();
        Debug.Log("LogicManager component found and assigned.");
    }

    private void OnTriggerEnter2D(Collider2D collision)
    {
        // Only add score when the Bird passes through the middle trigger
        // Option A: using tag "Bird"
        
        Debug.Log("Bird passed the middle!");
        if (collision.CompareTag("Bird"))
        {
            logic.AddScore(1);
            Debug.Log("Bird passed the middle! +1 score");
        }

        // If you prefer using a layer like in some tutorials, use this instead:
        // if (collision.gameObject.layer == 3)
        // {
        //     logic.AddScore(1);
        //     Debug.Log("Bird passed the middle! +1 score");
        // }
    }
}