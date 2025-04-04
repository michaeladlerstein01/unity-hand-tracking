using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using System.Threading;

public class MyListener : MonoBehaviour
{
    Thread thread;
    public int connectionPort = 25001;
    TcpListener server;
    TcpClient client;
    bool running;


    readonly object positionLock = new object(); // <-- Add this line


    void Start()
    {
        // Receive on a separate thread so Unity doesn't freeze waiting for data
        ThreadStart ts = new ThreadStart(GetData);
        thread = new Thread(ts);
        thread.Start();
    }

void GetData()
{
    server = new TcpListener(IPAddress.Any, connectionPort);
    server.Start();
    running = true;

    while (running)
    {
        try
        {
            using (client = server.AcceptTcpClient())
            using (NetworkStream nwStream = client.GetStream())
            {
                byte[] buffer = new byte[client.ReceiveBufferSize];

                while (running && client.Connected)
                {
                    int bytesRead = nwStream.Read(buffer, 0, buffer.Length);
                    if (bytesRead == 0) break; // client disconnected

                    string dataReceived = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                    if (!string.IsNullOrEmpty(dataReceived))
                    {
                        Vector3 parsed = ParseData(dataReceived);
                        lock (positionLock)
                        {
                            position = parsed;
                        }

                        byte[] response = Encoding.UTF8.GetBytes("OK");
                        nwStream.Write(response, 0, response.Length);
                    }
                }
            }
        }
        catch (SocketException e)
        {
            Debug.LogWarning("Socket exception: " + e.Message);
        }
    }

    server.Stop();
}

    void Connection()
    {
        // Read data from the network stream
        NetworkStream nwStream = client.GetStream();
        byte[] buffer = new byte[client.ReceiveBufferSize];
        int bytesRead = nwStream.Read(buffer, 0, client.ReceiveBufferSize);

        // Decode the bytes into a string
        string dataReceived = Encoding.UTF8.GetString(buffer, 0, bytesRead);
        
        // Make sure we're not getting an empty string
        //dataReceived.Trim();
        if (dataReceived != null && dataReceived != "")
        {
            // Convert the received string of data to the format we are using
            position = ParseData(dataReceived);
            nwStream.Write(buffer, 0, bytesRead);
        }
    }

    // Use-case specific function, need to re-write this to interpret whatever data is being sent
    public static Vector3 ParseData(string dataString)
    {
        Debug.Log(dataString);
        // Remove the parentheses
        if (dataString.StartsWith("(") && dataString.EndsWith(")"))
        {
            dataString = dataString.Substring(1, dataString.Length - 2);
        }

        // Split the elements into an array
        string[] stringArray = dataString.Split(',');

        // Store as a Vector3
        Vector3 result = new Vector3(
            float.Parse(stringArray[0]),
            float.Parse(stringArray[1]),
            float.Parse(stringArray[2]));

        return result;
    }

    // Position is the data being received in this example
    Vector3 position = Vector3.zero;

    void Update()
    {
        // Set this object's position in the scene according to the position received
        transform.position = position;
    }
}