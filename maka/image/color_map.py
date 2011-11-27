'''
Created on Jul 24, 2011

@author: sean
'''

import pyopencl as cl #@UnresolvedImport
from maka.cl_pipe import ComputationalPipe
import numpy as np

COLORMAPS = dict(
    gray={'blue': [[0.0, 0, 0], [1.0, 1, 1]],
            'green': [[0.0, 0, 0], [1.0, 1, 1]],
            'red': [[0.0, 0, 0], [1.0, 1, 1]]},
    
    jet={'blue': [[0.0, 0.5, 0.5],
      [0.11, 1, 1],
      [0.34, 1, 1],
      [0.65, 0, 0],
      [1, 0, 0]],
     'green': [[0.0, 0, 0],
      [0.125, 0, 0],
      [0.375, 1, 1],
      [0.64, 1, 1],
      [0.91, 0, 0],
      [1, 0, 0]],
     'red': [[0.0, 0, 0], [0.35, 0, 0], [0.66, 1, 1], [0.89, 1, 1], [1, 0.5, 0.5]]},
                 
    copper={'blue': [[0.0, 0.0, 0.0], [1.0, 0.4975, 0.4975]],
            'green': [[0.0, 0.0, 0.0], [1.0, 0.7812, 0.7812]],
            'red': [[0.0, 0.0, 0.0], [0.809524, 1.0, 1.0], [1.0, 1.0, 1.0]]}
                 
                 )

class ColorMap(ComputationalPipe):
    src = """
    uchar map_color(float norm, __global const float4* cmap);
    
    uchar map_color(float norm, __global const float4* cmap) {
        
        float low, high, lin;
        __global const float4* tmp = cmap;
        while (tmp[0].w == 0){
            if (tmp[1].x >= norm) {
                break;
            }
            tmp++;
        }
        
        uchar result;
        if (tmp[0].w == 1) {
            result = tmp[0].y * 255;
        } else {

            lin = (norm - tmp[0].x) / (tmp[1].x - tmp[0].x);
            
            low = tmp[0].z * 255;
            high = tmp[1].y * 255;
            
            result = (uchar) ((lin * (high - low)) + low);
    
        }
        
    
        return result;
    }
    
    __kernel void colormap(__global const float* data, __global uchar4* image, 
                          __global const float4* red_map, 
                          __global const float4* green_map, 
                          __global const float4* blue_map,
                          float ulimit_lower, float ulimit_upper)
    {
        //float lin;
        uchar4 result = (uchar4)(0,0,0,0);
        int idx = get_global_id(0);
        int idy = get_global_id(1);
        
        int nx = get_global_size(0);
        // int ny = get_global_size(1);
        
        int id = idx + nx * idy;
        
        float norm = (data[id] - ulimit_lower) / (ulimit_upper-ulimit_lower);
        
        result.x = map_color(norm, red_map);
        result.y = map_color(norm, blue_map);
        result.z = map_color(norm, green_map);
        
        image[idx + nx * idy] = result;
        
    }
    """

    def __init__(self, gl_context, cl_context, cdict, cl_data, cl_image, shape, clim):
        
        self.cl_data = cl_data
        self.cl_image = cl_image

        kernel = cl.Program(cl_context, self.src).build().colormap


        self._cdict = cdict
        self._cl_maps = {'red': self.create_cl_map(cl_context, cdict['red']),
                         'blue': self.create_cl_map(cl_context, cdict['blue']),
                          'green':self.create_cl_map(cl_context, cdict['green']),
                          }

        ComputationalPipe.__init__(self, gl_context, cl_context, shape, None, kernel,
                                   self.cl_data, self.cl_image,
                                   self._cl_maps['red'], self._cl_maps['blue'], self._cl_maps['green'],
                                   clim[0], clim[1])
    
    def set_cdict(self, cdict):

        self._cdict = cdict
        self._cl_maps = {'red': self.create_cl_map(self.cl_context, cdict['red']),
                         'blue': self.create_cl_map(self.cl_context, cdict['blue']),
                          'green':self.create_cl_map(self.cl_context, cdict['green']),
                          }

        self.kernel_args[2:5] = self._cl_maps['red'], self._cl_maps['blue'], self._cl_maps['green'] 
        
    def create_cl_map(self, cl_context, cmap):

        data = np.array([list(item) + [0] for item in cmap], dtype=np.float32)
        data[-1, -1] = 1
        cl_map = cl.Buffer(cl_context, cl.mem_flags.READ_WRITE, data.nbytes)

        queue = cl.CommandQueue(cl_context)
        cl.enqueue_copy(queue, cl_map, data)
        queue.finish()

        return cl_map



