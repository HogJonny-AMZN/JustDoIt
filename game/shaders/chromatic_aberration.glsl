// chromatic_aberration.glsl — RGB channel split post-process pass
// Uniforms: u_texture (sampler2D), u_offset (float)
// TODO: sample R/G/B channels at offset UV positions and recombine

#version 330

in vec2 v_uv;
out vec4 out_color;

uniform sampler2D u_texture;
uniform float     u_offset;

void main() {
    out_color = texture(u_texture, v_uv);  // passthrough — replace with CA effect
}
