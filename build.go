package main

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"os"
	"strings"
)

func Throw(err error) {
	if err != nil {
		panic(err)
	}
}

func CopyIndexHtml() {
	var err error

	var echarts_js_new string
	var echarts_js_old string
	{
		var content []byte
		content, err = ioutil.ReadFile("static/echarts.min.js")
		Throw(err)

		echarts_js_old = `<script type="text/javascript" src="static/echarts.min.js"></script>`
		echarts_js_new = fmt.Sprintf("<script>%s</script>", strings.ReplaceAll(string(content), "`", "there_is_a_backtick"))
	}

	var grids_responsive_css_old string
	var grids_responsive_css_new string
	{
		var content []byte
		content, err = ioutil.ReadFile("static/grids-responsive-min.css")
		Throw(err)

		grids_responsive_css_old = `<link rel="stylesheet" href="static/grids-responsive-min.css" />`
		grids_responsive_css_new = fmt.Sprintf("<style>%s</style>", string(content))
	}

	var pure_css_old string
	var pure_css_new string
	{
		var content []byte
		content, err = ioutil.ReadFile("static/pure-min.css")
		Throw(err)

		pure_css_old = `<link rel="stylesheet" href="static/pure-min.css" />`
		pure_css_new = fmt.Sprintf("<style>%s</style>", string(content))
	}

	var file *os.File
	file, err = os.Open("template/index.html")
	defer file.Close()
	Throw(err)

	var file2 *os.File
	file2, err = os.Create("build/index.html")
	defer file2.Close()
	Throw(err)

	var scanner *bufio.Scanner
	scanner = bufio.NewScanner(file)

	var writer *bufio.Writer
	writer = bufio.NewWriter(file2)

	for scanner.Scan() {
		var text string
		text = scanner.Text()

		if strings.HasSuffix(text, echarts_js_old) {
			_, err = writer.WriteString(echarts_js_new + "\n")
		} else if strings.HasSuffix(text, grids_responsive_css_old) {
			_, err = writer.WriteString(grids_responsive_css_new + "\n")
		} else if strings.HasSuffix(text, pure_css_old) {
			_, err = writer.WriteString(pure_css_new + "\n")
		} else {
			_, err = writer.WriteString(text + "\n")
		}
		Throw(err)
	}
	err = scanner.Err()
	Throw(err)

	err = writer.Flush()
	Throw(err)
}

func CopyLnxmonsrvGo() {
	var err error

	var content []byte
	content, err = ioutil.ReadFile("build/index.html")
	Throw(err)

	var html_new string
	html_new = fmt.Sprintf("HTML = `%s`", string(content))

	var html_old string
	html_old = `HTML = ""`

	var file *os.File
	file, err = os.Open("lnxmonsrv.go")
	defer file.Close()
	Throw(err)

	var file2 *os.File
	file2, err = os.Create("build/lnxmonsrv.go")
	defer file2.Close()
	Throw(err)

	var scanner *bufio.Scanner
	scanner = bufio.NewScanner(file)

	var writer *bufio.Writer
	writer = bufio.NewWriter(file2)

	for scanner.Scan() {
		var text string
		text = scanner.Text()

		if strings.HasSuffix(text, html_old) {
			_, err = writer.WriteString(html_new + "\n")
		} else {
			_, err = writer.WriteString(text + "\n")
		}
		Throw(err)
	}
	err = scanner.Err()
	Throw(err)

	err = writer.Flush()
	Throw(err)
}

func CopyLnxmoncliGo() {
	var err error

	var content []byte
	content, err = ioutil.ReadFile("lnxmoncli.go")
	Throw(err)

	err = ioutil.WriteFile("build/lnxmoncli.go", content, 0644)
	Throw(err)
}

func DeleteIndexHtml() {
	var err error
	err = os.Remove("build/index.html")
	Throw(err)
}

func main() {
	CopyIndexHtml()
	CopyLnxmonsrvGo()
	CopyLnxmoncliGo()
	DeleteIndexHtml()
}
