FROM registry.fedoraproject.org/fedora
# s2i needs tar command inside the image

LABEL io.openshift.s2i.scripts-url="image:///usr/libexec/s2i"

COPY ./.s2i/bin/ /usr/libexec/s2i

CMD ["usage"]
