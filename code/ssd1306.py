import framebuf


SET_CONTRAST = 0x81
SET_ENTIRE_ON = 0xA4
SET_NORM_INV = 0xA6
SET_DISP = 0xAE
SET_MEM_ADDR = 0x20
SET_COL_ADDR = 0x21
SET_PAGE_ADDR = 0x22
SET_DISP_START_LINE = 0x40
SET_SEG_REMAP = 0xA0
SET_MUX_RATIO = 0xA8
SET_COM_OUT_DIR = 0xC0
SET_DISP_OFFSET = 0xD3
SET_COM_PIN_CFG = 0xDA
SET_DISP_CLK_DIV = 0xD5
SET_PRECHARGE = 0xD9
SET_VCOM_DESEL = 0xDB
SET_CHARGE_PUMP = 0x8D


class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        # Initializes the shared SSD1306 frame buffer state.
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        # Sends the standard SSD1306 initialization command sequence.
        for command in (
            SET_DISP,
            SET_MEM_ADDR,
            0x00,
            SET_DISP_START_LINE,
            SET_SEG_REMAP | 0x01,
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,
            SET_CONTRAST,
            0xFF,
            SET_ENTIRE_ON,
            SET_NORM_INV,
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,
        ):
            self.write_cmd(command)
        self.fill(0)
        self.show()

    def poweroff(self):
        # Turns the OLED panel off.
        self.write_cmd(SET_DISP)

    def poweron(self):
        # Turns the OLED panel on.
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        # Sets OLED contrast from 0 to 255.
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        # Switches normal or inverted pixel mode.
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        # Flushes the frame buffer to the display memory.
        left_column = 0
        right_column = self.width - 1
        if self.width == 64:
            left_column += 32
            right_column += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(left_column)
        self.write_cmd(right_column)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        # Initializes an SSD1306 display connected by I2C.
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]
        super().__init__(width, height, external_vcc)

    def write_cmd(self, command):
        # Writes one command byte over I2C.
        self.temp[0] = 0x80
        self.temp[1] = command
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buffer):
        # Writes the frame buffer bytes over I2C.
        self.write_list[1] = buffer
        self.i2c.writevto(self.addr, self.write_list)
