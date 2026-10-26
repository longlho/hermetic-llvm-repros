template <class First, class... Rest>
union RecursiveUnion {
    First first;
    RecursiveUnion<Rest...> rest;
};

template <class First>
union RecursiveUnion<First> {
    First first;
};
