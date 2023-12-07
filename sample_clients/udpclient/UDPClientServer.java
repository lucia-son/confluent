import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.Scanner;

public class UDPClientServer {
    public static void main(String[] args) {


        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        startClient();
    }

    public static void startClient() {
        DatagramSocket socket = null;

        try {
            socket = new DatagramSocket();

            Scanner scanner = new Scanner(System.in);
            System.out.print("메시지를 입력 하시오 : ");
            String message = scanner.nextLine();

            byte[] sendData = message.getBytes();

            InetAddress serverAddress = InetAddress.getByName("localhost");
            int serverPort = 8888;

            DatagramPacket sendPacket = new DatagramPacket(sendData, sendData.length, serverAddress, serverPort);
            socket.send(sendPacket);

            System.out.println("Message from Client : " + message);
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (socket != null) {
                socket.close();
            }
        }
    }
}


