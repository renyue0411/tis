package main

import (
	"crypto/tls"
	"fmt"
	"os"
	"strconv"
	"time"

	//"bufio"

	config "../config"
	utils "../utils"
	quic "github.com/lucas-clemente/quic-go"
	//quic "github.com/lucas-clemente/pstream"
)

// const addr = config.SERVER_ADDR
const threshold = 10 * 1024 // 10KB
//TODO: set this threshold dynamically, based on network conditions

func main() {

	quicConfig := &quic.Config{
		CreatePaths: true,
		//Scheduler: 'round_robin',

		HandshakeTimeout: 30 * time.Second,
		IdleTimeout:      60 * time.Second,
	}

	//fileToSend := "./1GB.bin"
	//fileToSend := "./512MB.zip"
	//fileToSend := "./100MB.bin"
	//fileToSend := "./250MB.zip"
	fileToSend := "/home/server/Desktop/MPQUICFileTransfer/file-transfer/client/20MB.zip"
	//addr := "192.168.22.2:6667"
	//addr := "54.168.83.242:6666"
	// addr := "127.0.0.1:8080"
	addr := "10.1.0.1:8080"
	//fileToSend := os.Args[1]
	//addr := os.Args[2] + ":6666"

	// reader := bufio.NewReader(os.Stdin)
	// fmt.Print("Filename (blank for dummyfile.txt): ")
	// text, _ := reader.ReadString('\n')

	// if text != "\n" {
	//     fileToSend = text[:len(text) - 1]
	// }
	fmt.Println("Server Address: ", addr)
	fmt.Println("Sending File: ", fileToSend)

	file, err := os.Open(fileToSend)
	utils.HandleError(err)

	fileInfo, err := file.Stat()
	utils.HandleError(err)

	if fileInfo.Size() <= threshold {
		quicConfig.CreatePaths = false
		fmt.Println("File is small, using single path only.")
	} else {
		fmt.Println("file is large, using multipath now.")
	}
	//if fileInfo.Size() <= threshold && quicConfig.CreatePaths{
	//quicConfig.CreatePaths = false
	//fmt.Println("Both interface is working.")
	//} else{

	//fmt.Println("one interface is working.")
	//}
	file.Close()

	fmt.Println("Trying to connect to: ", addr)
	sess, err := quic.DialAddr(addr, &tls.Config{InsecureSkipVerify: true}, quicConfig)
	utils.HandleError(err)

	fmt.Println("session created: ", sess.RemoteAddr())

	stream, err := sess.OpenStream()
	utils.HandleError(err)

	fmt.Println("stream created...")
	fmt.Println("Client connected")
	sendFile(stream, fileToSend)
	time.Sleep(2 * time.Second)

}

func sendFile(stream quic.Stream, fileToSend string) {
	fmt.Println("A client has connected!")
	defer stream.Close()

	file, err := os.Open(fileToSend)
	utils.HandleError(err)

	fileInfo, err := file.Stat()
	utils.HandleError(err)

	fileSize := utils.FillString(strconv.FormatInt(fileInfo.Size(), 10), 10)
	fileName := utils.FillString(fileInfo.Name(), 64)

	fmt.Println("Sending filename and filesize!")
	stream.Write([]byte(fileSize))
	stream.Write([]byte(fileName))

	sendBuffer := make([]byte, config.BUFFERSIZE)
	fmt.Println("Start sending file!")

	var sentBytes int64
	start := time.Now()

	for {
		sentSize, err := file.Read(sendBuffer)
		if err != nil {
			break
		}

		stream.Write(sendBuffer)
		if err != nil {
			break
		}

		sentBytes += int64(sentSize)
		fmt.Printf("\033[2K\rSent: %d / %d", sentBytes, fileInfo.Size())
	}
	elapsed := time.Since(start)
	file_result, err := os.OpenFile(
		"transfer_time.txt",
		os.O_APPEND|os.O_CREATE|os.O_WRONLY,
		0644,
	)
	if err != nil {
		panic(err)
	}
	defer file_result.Close()
	fmt.Fprintf(file_result, "%.6f\n", elapsed.Seconds())
	fmt.Println("\nTransfer took: ", elapsed)
	stream.Close()
	fmt.Println("\n\nFile has been sent, closing stream!")
	return
}
