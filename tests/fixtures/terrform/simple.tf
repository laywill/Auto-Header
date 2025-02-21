variable "region" {
  type    = string
  default = "us-west-2"
}

resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
}
