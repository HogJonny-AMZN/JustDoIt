// bloom.glsl — luminance-threshold bloom post-process pass
// Uniforms: u_texture (sampler2D), u_threshold (float), u_intensity (float)
// TODO: extract bright pixels, gaussian blur, additive blend back

#version 330

in vec2 v_uv;
out vec4 out_color;

uniform sampler2D u_texture;
uniform float     u_threshold;
uniform float     u_intensity;

void main() {
    out_color = texture(u_texture, v_uv);  // passthrough — replace with bloom
}
