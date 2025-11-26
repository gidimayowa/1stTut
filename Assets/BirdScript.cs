using UnityEngine;

public class BirdScript : MonoBehaviour
{
    public float jumpForce = 20.0f;
    private Rigidbody2D myRigidbody;
    private CircleCollider2D myCollider;
    public LogicManager logic;
    public bool birdIsAlive = true;

    void Awake()
    {
        
        logic = GameObject.FindGameObjectWithTag("Logic").GetComponent<LogicManager>();
        myRigidbody = GetComponent<Rigidbody2D>();
        myCollider = GetComponent<CircleCollider2D>();
        if (myRigidbody == null)
        {
            Debug.LogError("Rigidbody2D component is missing on " + gameObject.name);
        }
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space)&&birdIsAlive)
        {
            Debug.Log("Space pressed – trying to jump");
            Jump();
        }
    }

    private void Jump()
    {
        if (myRigidbody != null)
        {
            myRigidbody.linearVelocity = new Vector2(myRigidbody.linearVelocity.x, jumpForce);
        }
    }

    private void OnCollisionEnter2D(Collision2D collision)
    {
        // Only react if we hit something tagged "Pipe"
        if (collision.collider.CompareTag("Pipe"))
        {
            Debug.Log("Birdie hit a PIPE!");
            logic.gameOver();
            Debug.Log("Game Over");
            birdIsAlive = false;
            // Here you can also call game over logic later
        }
    }

}
