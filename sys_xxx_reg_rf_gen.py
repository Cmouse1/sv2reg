import sys
sys.path.append('.')
from address_planner import *

regBank = RegSpace(name='sys_xxx',size=16*KB,description="top register block",bus_width=16,software_interface='apb')

##### ctrl #####
reg_0 = Register(name='ctrl',bit=32,description="control registers",reg_type=Normal, parity=True)
reg_0.add(Field(name='rst_n',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0,description='reset'),offset = 0)
reg_0.add(Field(name='mode',bit=3,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b000,description='mode select'),offset = 1)
reg_0.add(Field(name='enable',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0,description='enable switch'),offset = 4)
reg_0.add(Field(name='status',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,init_value=0b0,description='status flag'),offset = 5)
reg_0.add(Field(name='version',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,init_value=0b0000,description='version number'),offset = 6)
regBank.add(reg_0, offset=0x00)

##### dma #####
reg_1 = Register(name='dma',bit=32,description="dma engine config",reg_type=Normal, parity=True)
reg_1.add(Field(name='src_addr',bit=32,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b00000000000000000000000000000000,description='source address'),offset = 0)
regBank.add(reg_1, offset=0x04)

reg_2 = Register(name='dma_ex0',bit=32,description="dma engine config",reg_type=Normal, parity=True)
reg_2.add(Field(name='dst_addr',bit=32,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b00000000000000000000000000000000,description='destination address'),offset = 0)
regBank.add(reg_2, offset=0x08)

reg_3 = Register(name='dma_ex1',bit=32,description="dma engine config",reg_type=Normal, parity=True)
reg_3.add(Field(name='tx_len',bit=16,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0000000000000000,description='transfer length'),offset = 0)
reg_3.add(Field(name='done',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,init_value=0b0,description='transfer done'),offset = 16)
regBank.add(reg_3, offset=0x0C)

##### intr #####
reg_4 = Register(name='intr',bit=32,description="interrupt",reg_type=Normal, parity=True)
reg_4.add(Field(name='intr_en',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0,description='interrupt enable'),offset = 0)
reg_4.add(Field(name='intr_pend',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,init_value=0b0,description='interrupt pending'),offset = 1)
reg_4.add(Field(name='intr_clr',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0,description='interrupt clear'),offset = 2)
regBank.add(reg_4, offset=0x10)

##### spare #####
reg_5 = Register(name='spare',bit=32,description="spare registers",reg_type=Normal, parity=True)
reg_5.add(Field(name='spare_0',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0,description='spare 0'),offset = 0)
reg_5.add(Field(name='spare_1',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,init_value=0b0,description='spare 1'),offset = 1)
regBank.add(reg_5, offset=0x14)

##### override #####
reg_6 = Register(name='override',bit=32,description="manual access override",reg_type=Normal, parity=True)
reg_6.add(Field(name='ro_reg',bit=1,sw_access=ReadOnly,hw_access=ReadOnly,init_value=0b0,description='force RO'),offset = 0)
reg_6.add(Field(name='rw_reg',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,init_value=0b0,description='force RW'),offset = 1)
reg_6.add(Field(name='hw_only',bit=1,sw_access=ReadWrite,hw_access=WriteOnly,init_value=0b0,description='hw write only'),offset = 2)
regBank.add(reg_6, offset=0x18)

if __name__ == "__main__":
    regBank.generate('build')