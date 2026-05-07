// crt.glsl — CRT scanline + barrel distortion post-process pass
// Uniforms: u_texture (sampler2D), u_resolution (vec2), u_time (float)
// TODO: implement scanlines, barrel distortion, vignette

#version 330

in vec2 v_uv;
out vec4 out_color;

uniform sampler2D u_texture;
uniform vec2      u_resolution;
uniform float     u_time;

void main() {
    out_color = texture(u_texture, v_uv);  // passthrough — replace with CRT effect
}
