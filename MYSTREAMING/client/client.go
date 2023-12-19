package main

import (
	"crypto/tls"
	"encoding/binary"
	"fmt"
	"io"
	"log"
	random "math/rand"
	"sync"
	"time"

	config "../config"
	utils "../utils"
	quic "github.com/lucas-clemente/quic-go"
	"gocv.io/x/gocv"
)

const addr = config.IP + ":" + config.PORT
const deviceID = 0

// CHUNK size to read
// const CHUNK = 1024 * 10
var (
	err     error
	webcam  *gocv.VideoCapture
	size1   int64 //send
	size2   int64 //receive
	elapsed time.Duration
)

func main() {
	client(addr)
}

func client(addr string) {
	// setup multipath configuration
	quicConfig := &quic.Config{
		CreatePaths: true,
	}
	// connect to server
	session, err := quic.DialAddr(addr, &tls.Config{InsecureSkipVerify: true}, quicConfig)
	utils.HandleError(err)
	fmt.Println("Connection established with server successfully.")

	stream, err := session.AcceptStream()
	utils.HandleError(err)
	fmt.Println("Broadcasting incoming video stream.")
	defer stream.Close()

	// Test
	// camReceiveTest(stream)
	// camReceive(stream)

	// Multi-threading
	var wg sync.WaitGroup
	wg.Add(2)
	go camSend(&wg, stream)
	fmt.Println("Starting cam stream.")
	go camReceive(&wg, stream)
	wg.Wait()
}

func camSend(wg *sync.WaitGroup, stream quic.Stream) {
	defer wg.Done()
	webcam, err := gocv.OpenVideoCapture(deviceID)

	if err != nil {
		fmt.Printf("Error opening capture device: %v\n", deviceID)
		return
	}
	defer webcam.Close()

	var length = 0

	//an infinite loop that generates frames from the webcam and sends to reciever

	img := gocv.NewMat()
	defer img.Close()

	var image_count = 0

	t := time.Now()
	var t1, t2 time.Duration = 0, 0

	for {

		if image_count%20 == 0 { //fps is calculated if 100 image is transmitted
			t = time.Now()
			size1 = 0
		}
		if image_count == 1001 {
			break
		}

		// read the image from the device
		if ok := webcam.Read(&img); !ok {
			fmt.Printf("Device closed: %v\n", deviceID)
			return
		}
		if img.Empty() {
			continue
		}

		t3 := time.Now()                     //t3 is to calculate the time  gocv consumed when an image is endoded
		buf, _ := gocv.IMEncode(".jpg", img) // encode the imgae into byte[] for transport
		buf2 := buf.GetBytes()

		timeStamp := make([]byte, 8) //the current time
		binary.LittleEndian.PutUint64(timeStamp, uint64(time.Now().UnixMilli()))
		buf2 = append(buf2, timeStamp...)
		length = len(buf2)
		size1 += int64(length)
		t1 += time.Since(t3)

		bs := make([]byte, 8)
		binary.LittleEndian.PutUint32(bs, uint32(length)) //encoding the length(integer) as a byte[] for transport

		//fmt.Println(image_count)

		image_count = image_count + 1

		stream.Write(bs) //sends the length of the frame so that appropriate buffer size can be created in the reciever side

		time.Sleep(time.Second / 1000) //time delay of 10 milli second

		t4 := time.Now()
		stream.Write(buf2) //sends the frame

		t2 += time.Since(t4)
		if image_count%20 == 0 {
			elapsed := time.Since(t)
			duration := float64(elapsed) / float64(time.Second)
			fmt.Println("==================================SEND==================================")
			log.Println("FPS:", 20/(duration))
			log.Println("throughput(MB):", float64(size1)/(1024.0*1024.0*float64(duration)))
			log.Println("gocv time :", t1, "transfer time :", t2, "total time:", elapsed)
			t1, t2 = 0, 0
		}
	}
}

func camReceive(wg *sync.WaitGroup, stream quic.Stream) {
	defer wg.Done()

	window := gocv.NewWindow("Capture Window")
	defer window.Close()

	frame_counter := 0
	t := time.Now()
	var t1, t2 time.Duration = 0, 0
	for {
		if frame_counter%20 == 0 {
			t = time.Now()
			size2 = 0
		}
		siz := make([]byte, 8) // size is needed to make use of ReadFull(). ReadAll() needs EOF to stop accepting while ReadFull just needs the fixed size.

		_, err := io.ReadFull(stream, siz)      //recieve the size
		data := binary.LittleEndian.Uint64(siz) //if the first few bytes contain the length; else use BigEndian or reverse the byte[] and use LittleEndian
		utils.HandleError(err)

		if data == 0 {
			defer stream.Close()
			return
		}
		t4 := time.Now()
		buff := make([]byte, data)
		size2 += int64(data)
		len2, err := io.ReadFull(stream, buff) // recieve image

		t2 += time.Since(t4)
		utils.HandleError(err)

		//if empty buffer
		if len2 == 0 {
			defer stream.Close()
			return
		}

		//calculate the time of this image from the webcam to this client
		imgbuff := buff[0 : len2-8]
		timeStamp := buff[len2-8 : len2]
		clientTime := binary.LittleEndian.Uint64(timeStamp)
		//fmt.Println(clientTime)
		//fmt.Println(" the time :",uint64(time.Now().UnixMilli())-clientTime)//the time consumed

		img, err := gocv.IMDecode(imgbuff, 1) //IMReadFlag 1 ensure that image is converted to 3 channel RGB

		utils.HandleError(err)
		// if decoding fails

		if img.Empty() {
			defer stream.Close()
			return
		}

		random.Seed(time.Now().UnixNano())
		num := random.Intn(10)
		if num == 5 {
			clientTime++
			//log.Println("time consumed :", uint64(time.Now().UnixMilli())-clientTime)
		}

		t3 := time.Now()

		window.IMShow(img)

		t1 += time.Since(t3)

		if window.WaitKey(1) == 27 {
			break
		}

		frame_counter += 1
		if frame_counter%20 == 0 {
			elapsed = time.Since(t)
			duration := float64(elapsed) / float64(time.Second)
			fmt.Println("==================================RECEIVE==================================")
			log.Println("FPS:", 20/(duration))
			log.Println("throughput(MB):", float64(size2)/(1024.0*1024.0*float64(duration)))
			log.Println("gocv time :", t1, "transfer time :", t2, "total time:", elapsed)
			t1, t2 = 0, 0
			//log.Println("FPS:",100 / (int(elapsed / time.Second)))
		}
		/*fmt.Println(videoDir + "/img" + strconv.Itoa(frame_counter) + ".jpg")

		file.Close()*/
	}
}

func sendMessage(msg string, stream quic.Stream) {
	// utility for sending control messages
	l := uint32(len(msg))
	data := make([]byte, 4)
	binary.LittleEndian.PutUint32(data, l)
	stream.Write(data)
	stream.Write([]byte(msg))
}

func readMessage(stream quic.Stream) string {
	// utility for receiving control messages
	data := make([]byte, 4)
	stream.Read(data)
	l := binary.LittleEndian.Uint32(data)
	data = make([]byte, l)
	stream.Read(data)
	return string(data)
}

