from torch.autograd import Variable
from collections import OrderedDict
import util.util as util
from .base_model import BaseModel
from . import networks
import numpy as np

class TestModel(BaseModel):
    def name(self):
        return 'TestModel'

    def initialize(self, opt):
        assert(not opt.isTrain)
        BaseModel.initialize(self, opt)
        self.input_A = self.Tensor(
            opt.batchSize, opt.input_nc, opt.fineSize, opt.fineSize)

        self.netG = networks.define_G(opt.input_nc, opt.output_nc, opt.ngf,
                                      opt.which_model_netG, opt.norm, not opt.no_dropout, self.gpu_ids, False,
                                      opt.learn_residual)
        which_epoch = opt.which_epoch
        print(which_epoch)
        print("sss")
        self.load_network(self.netG, 'G', which_epoch)

        print('---------- Networks initialized -------------')
        networks.print_network(self.netG)
        print('-----------------------------------------------')

    def set_input(self, input):
        # we need to use single_dataset mode
        input_A = input['A']
        temp = self.input_A.clone()
        temp.resize_(input_A.size()).copy_(input_A)
        self.input_A = temp
        self.image_paths = input['A_paths']
        print(self.image_paths,"ffdddddffe")


    def test(self):
        self.real_A = Variable(self.input_A)
        self.fake_B = self.netG.forward(self.real_A)

    # get image paths
    def get_image_paths(self):
        print(self.image_paths,"get_image_paths")
        return self.image_paths

    def get_current_visuals(self):
        real_A = util.tensor2im(self.real_A.data)
        fake_B = util.tensor2im(self.fake_B.data)
        print(type(real_A),"get_current_visuals")
        concatenate = np.concatenate((real_A,fake_B),axis=1)
        return OrderedDict([('real_A', real_A), ('fake_B', fake_B)])

    def get_current_visuals_test(self):
        real_A = util.tensor2im(self.real_A.data)
        fake_B = util.tensor2im(self.fake_B.data)
        print(type(real_A),"get_current_visuals")
        concatenate = np.concatenate((real_A,fake_B),axis=1)
        return OrderedDict([('real_A', real_A), ('fake_B', fake_B),('concatenate',concatenate)])